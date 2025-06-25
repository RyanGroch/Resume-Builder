import sys
import json
import os
import shutil
import subprocess
from pathlib import Path

# Contains all of the resume components
DATA = json.loads(Path("data.json").read_text())

# Templates for sections of LaTeX files
RESUME_TEMPL = Path("templates/resume-template.txt").read_text()
SECTION_TEMPL = Path("templates/section-template.txt").read_text()
PROJECT_TEMPL = Path("templates/project-template.txt").read_text()
EXP_TEMPL = Path("templates/experience-template.txt").read_text()
EDU_TEMPL = Path("templates/education-template.txt").read_text()

# Single-line templates for import statements, bullet points, etc.
IMPORT_TOKEN = "\\input{{resume/{name}.tex}}\n"
BOLD_ITEM_TOKEN = "\\textbf{{{skill_category}}}: {content}"
BULLET_ITEM_TOKEN = "\\item {{{item}}}"
INDENTED_BULLET_ITEM_TOKEN = "\\hspace{{{space}}} \\bullet \\hspace{{1mm}} {item}"
LINE_BREAK_TOKEN = " \\\\ \n"
NEWLINE_TOKEN = " \\newline\n" + 8 * " "

# Describes the levels of indent that a bullet point can have
INDENT_HIERARCHY = [
    None,
    "1mm",
    "5mm",
    "9mm",
    "13mm"
]

# Section types - defined by Awesome CV for formatting purposes
PARAGRAPH = "cvparagraph"
ENTRIES = "cventries"


def render_indented_points(point, include, exclude, indent_level=-1):
    """Forms a string containing LaTeX code to produce indented bullet points.

    Arguments:

    point -- A string or a dictionary. Strings will be converted to
        LaTeX code. Dictionaries indicate that the level of indentation
        will be increased. Dictionaries may include additional strings
        or other dictionaries, and are processed recursively.

    include -- A list containing the dictionary keys of the bullet
        points that this function should render. Can also be None.
        If it's a list, then only the bullet points in that list
        will be converted to LaTeX code. If it's None, 
        then by default all bullet points will be included.

    exclude -- A list containing dictionary keys of the bullet
        points that this function should NOT render. Can also
        be None. If it's None, then all of the points in the
        include list will be rendered to LaTeX. Exclude takes
        higher precendence over the include list.

    indent_level -- An integer representing an index of the
        INDENT_HIERARCHY array. 
    """
    if isinstance(point, dict):
        included_points = point.items() if not include else [
            (key, point[key]) for key in include 
            if point.get(key) is not None
        ]

        if exclude:
            included_points = filter(
                lambda curr_point: curr_point[0] not in exclude,
                included_points 
            )

        return NEWLINE_TOKEN.join([
            render_indented_points(
                value, 
                include,
                exclude,
                indent_level + 1, 
            )
            for _, value in included_points
        ])
    
    if INDENT_HIERARCHY[indent_level] is None:
        return BULLET_ITEM_TOKEN.format(item=point)
    
    return INDENTED_BULLET_ITEM_TOKEN.format(
        item=point,
        space=INDENT_HIERARCHY[indent_level]
    )   


def build_summary(recipe):
    """Generates LaTeX code for the 'Summary' section of the resume."""
    if "summary" not in recipe or not recipe["summary"]:
        return ""

    return DATA["summaries"][recipe["summary"]]


def build_skills(recipe):
    """Generates LaTeX code for the 'Skills' section of the resume."""
    return LINE_BREAK_TOKEN.join(
        map(lambda section: 
            BOLD_ITEM_TOKEN.format(
                skill_category=section["name"],
                content=", ".join(
                    [DATA["skills"][skill] for skill in section["content"]]
                )
            ),
            recipe["skills"]
        )
    )


def build_projects(recipe):
    """Generates LaTeX code for the 'Projects' section of the resume."""
    projects = []
        
    for project_recipe in recipe["projects"]:
        project = DATA["projects"][project_recipe['name']]

        points = render_indented_points(
            project["points"],
            project_recipe.get("include"),
            project_recipe.get("exclude")
        )

        if project["tech"]:
            tech = BULLET_ITEM_TOKEN.format(
                item=BOLD_ITEM_TOKEN.format(
                    skill_category="Technologies:",
                    content=project["tech"]
                )
            )
            points = tech + NEWLINE_TOKEN + points

        projects.append(
            PROJECT_TEMPL.format(
                href=project["href"],
                link=project["link"],
                name=project["name"],
                date=project["date"],
                content=points
            )
        )

    return "".join(projects)


def build_experience(recipe):
    """Generates LaTeX code for the 'Experience' section of the resume."""
    experiences = []
    for experience_recipe in recipe["experience"]:
        experience = DATA["experience"][experience_recipe["name"]]

        points_str = render_indented_points(
            experience["points"],
            experience_recipe.get("include"),
            experience_recipe.get("exclude")
        )

        experiences.append(EXP_TEMPL.format(
            name=experience[experience_recipe["title"]],
            employer=experience["employer"],
            date=experience["date"],
            content=points_str
        ))

    return "".join(experiences)


def build_education(recipe):
    """Generates LaTeX code for the 'Education' section of the resume."""
    educations = []
    for education_recipe in recipe["education"]:
        education = DATA["education"][education_recipe["name"]]

        educations.append(EDU_TEMPL.format(
            degree=education["degree"],
            institution=education["institution"],
            location=education["location"],
            date=education["date"],
            content=render_indented_points(
                education["points"],
                education_recipe.get("include"),
                education_recipe.get("exclude")
            )
        ))

    return "".join(educations)


# Allows us to loop through and build each of the sections
# Indices:
# 0 => Internal name/File name
# 1 => Printed name on the resume
# 2 => Whether the section is a paragraph or has "entries"
# 3 => Callback function to generate the LaTeX for the section
SECTIONS = [
    ("summary", "Objective", PARAGRAPH, build_summary),
    ("skills", "Skills", PARAGRAPH, build_skills),
    ("projects", "Projects", ENTRIES, build_projects),
    ("experience", "Experience", ENTRIES, build_experience),
    ("education", "Education", ENTRIES, build_education)
]


def main():
    """Generates and compiles the various pieces of the resume."""
    if len(sys.argv) < 2:
        print("Usage: python3 build.py recipe")
        return
    
    recipe_name = sys.argv[1]
    recipe_path = f"recipes/{recipe_name}.json"

    # Load information for the specific resume
    # that we want to compile
    try:
        recipe = json.loads(Path(recipe_path).read_text())

    except FileNotFoundError:
        print(f"Unrecognized recipe: {recipe_name}")
        return

    # Create fresh LaTeX project structure
    shutil.rmtree("build", ignore_errors=True)
    os.makedirs("build/resume", exist_ok=True)
    shutil.copyfile("templates/awesome-cv.cls", "build/awesome-cv.cls")

    # Generate entry point LaTeX code, which imports
    # all of the individual sections
    entry_point_content = RESUME_TEMPL.format(
        position=recipe["position"],
        content="".join([
            IMPORT_TOKEN.format(name=section[0]) 
            for section in SECTIONS 
            if recipe[section[0]]
        ])
    )

    # Write the entry point file
    with open("build/resume.tex", "w") as f:
        f.write(entry_point_content)

    # Write each of the LaTeX files
    # for the individual sections
    for section in SECTIONS:
        content = SECTION_TEMPL.format(
            section_name=section[1],
            section_type=section[2],
            content=section[3](recipe)
        )

        with open(f"build/resume/{section[0]}.tex", "w") as f: 
            f.write(content)

    # After the LaTeX code has been generated,
    # compile it into a resume
    subprocess.run(["xelatex", "resume.tex"], cwd="./build")


if __name__ == "__main__":
    main()
