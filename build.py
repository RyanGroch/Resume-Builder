import sys
import json
import os
import shutil
import subprocess
from pathlib import Path


DATA = json.loads(Path("data.json").read_text())
RECIPES = json.loads(Path("recipes.json").read_text())

RESUME_TEMPL = Path("templates/resume-template.txt").read_text()
SECTION_TEMPL = Path("templates/section-template.txt").read_text()
PROJECT_TEMPL = Path("templates/project-template.txt").read_text()
EXP_TEMPL = Path("templates/experience-template.txt").read_text()
EDU_TEMPL = Path("templates/education-template.txt").read_text()

IMPORT_TOKEN = "\input{{resume/{name}.tex}}\n"
BOLD_ITEM_TOKEN = "\\textbf{{{skill_category}}}: {content}"
BULLET_ITEM_TOKEN = "\\item {{{item}}}"
INDENTED_BULLET_ITEM_TOKEN = "\hspace{{{space}}} \\bullet \hspace{{1mm}} {item}"
LINE_BREAK_TOKEN = " \\\\ \n"
NEWLINE_TOKEN = " \\newline\n" + 8 * " "

INDENT_HIERARCHY = [
    None,
    "1mm",
    "5mm",
    "9mm",
    "13mm"
]

# Section types
PARAGRAPH = "cvparagraph"
ENTRIES = "cventries"


def render_indented_points(point, indent_level, exclude):
    if isinstance(point, dict):
        return NEWLINE_TOKEN.join([
            render_indented_points(
                value, 
                indent_level + 1, 
                exclude
            )
            for key, value in point.items()
            if key not in exclude
        ])
    
    if INDENT_HIERARCHY[indent_level] is None:
        return BULLET_ITEM_TOKEN.format(item=point)
    
    return INDENTED_BULLET_ITEM_TOKEN.format(
        item=point,
        space=INDENT_HIERARCHY[indent_level]
    )   


def build_summary(recipe):
    return DATA["summaries"][recipe["summary"]]


def build_skills(recipe):
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
    projects = []
        
    for project_recipe in recipe["projects"]:
        project = DATA["projects"][project_recipe['name']]
        points = render_indented_points(project["points"], -1, project_recipe["exclude"])

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
    experiences = []
    for experience_recipe in recipe["experience"]:
        experience = DATA["experience"][experience_recipe["name"]]

        points_str = render_indented_points(
            experience["points"],
            -1,
            experience_recipe["exclude"]
        )

        experiences.append(EXP_TEMPL.format(
            name=experience["name"],
            employer=experience["employer"],
            date=experience["date"],
            content=points_str
        ))

    return "".join(experiences)


def build_education(recipe):
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
                -1, 
                education_recipe["exclude"])
        ))

    return "".join(educations)


SECTIONS = [
    ("summary", "Objective", PARAGRAPH, build_summary),
    ("skills", "Skills", PARAGRAPH, build_skills),
    ("projects", "Projects", ENTRIES, build_projects),
    ("experience", "Experience", ENTRIES, build_experience),
    ("education", "Education", ENTRIES, build_education)
]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build.py recipe")
        return
    
    recipe_name = sys.argv[1]
    recipe = RECIPES[recipe_name]

    shutil.rmtree("build", ignore_errors=True)
    os.makedirs("build/resume", exist_ok=True)
    shutil.copyfile("templates/awesome-cv.cls", "build/awesome-cv.cls")

    with open("build/resume.tex", "w") as out_file:
        content = ""

        for section in SECTIONS:
            if recipe[section[0]]:
                content += IMPORT_TOKEN.format(name=section[0])
        
        out_file.write(RESUME_TEMPL.format(content=content))

    for section in SECTIONS:
        content = SECTION_TEMPL.format(
            section_name=section[1],
            section_type=section[2],
            content=section[3](recipe)
        )

        with open(f"build/resume/{section[0]}.tex", "w") as f: 
            f.write(content)

    subprocess.run(["xelatex", "resume.tex"], cwd="./build")


if __name__ == "__main__":
    main()
