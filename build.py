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
BOLD_ITEM_NEWLINE_TOKEN = f"{BOLD_ITEM_TOKEN} \\\\\n"
BULLET_ITEM_TOKEN = "\\item {{{item}}}"
INDENTED_BULLET_ITEM_TOKEN = "\hspace{{1mm}} \\bullet \hspace{{1mm}} {item} \\newline"

edu_std_point = "        \item {{{0}}}"
edu_custom_1 = "         {0} \\newline"
edu_custom_2 = "         \hspace{{1mm}} \\bullet \hspace{{1mm}} {0} \\newline"
edu_custom_3 = "         \hspace{{5mm}} \\bullet \hspace{{1mm}} {0} \\newline"

# Section types
PARAGRAPH = "cvparagraph"
ENTRIES = "cventries"


def build_summary(recipe):
    return DATA["summaries"][recipe["summary"]]


def build_skills(recipe):
    skills_str = ""
    for i, section in enumerate(recipe["skills"]):
        curr_skill_str = ""

        for j, skill in enumerate(section["content"]):
            if j != 0:
                curr_skill_str += ", "

            curr_skill_str += DATA["skills"][skill]

        token = BOLD_ITEM_NEWLINE_TOKEN \
            if i != len(recipe["skills"]) - 1 \
            else BOLD_ITEM_TOKEN

        skills_str += token.format(
            skill_category=section["name"],
            content=curr_skill_str
        )

    return skills_str


def build_projects(recipe):
    projects_str = ""
        
    for project_recipe in recipe["projects"]:
        project = DATA["projects"][project_recipe['name']]
        project_items_str = ""

        if project["tech"]:
            project_items_str += BULLET_ITEM_TOKEN.format(
                item=BOLD_ITEM_TOKEN.format(
                    skill_category="Technologies:",
                    content=project["tech"]
                )
            ) + "\n" + 8 * " "

        for i, (key, value) in enumerate(project["points"].items()):
            if key not in project_recipe["exclude"]:
                curr_proj_str = BULLET_ITEM_TOKEN.format(item=value)

                if i < len(project["points"]) - 1:
                    curr_proj_str += "\n"
                
                project_items_str += curr_proj_str + 8 * " "

        projects_str += PROJECT_TEMPL.format(
            href=project["href"],
            link=project["link"],
            name=project["name"],
            date=project["date"],
            content=(project_items_str)
        )

    return projects_str


def build_experience(recipe):
    exp_str = ""
    for experience_recipe in recipe["experience"]:
        experience = DATA["experience"][experience_recipe["name"]]
        curr_exp_str = ""
        
        for key, value in experience["points"].items():
            if key not in experience_recipe["exclude"]:
                if isinstance(value, dict):
                    for subval in value.values():
                        curr_exp_str += INDENTED_BULLET_ITEM_TOKEN.format(item=subval)
                else:
                    curr_exp_str += BULLET_ITEM_TOKEN.format(item=value) + "\\newline"

        exp_str += EXP_TEMPL.format(
            name=experience["name"],
            employer=experience["employer"],
            date=experience["date"],
            content=curr_exp_str
        )

    return exp_str


def build_education(recipe):
    education_str = ""
    for education_recipe in recipe["education"]:
        education = DATA["education"][education_recipe["name"]]

        points_str = ""
        for key, value in education["points"].items():
            if education["notation"] == "standard":
                points_str += edu_std_point.format(value)
            elif not isinstance(value, dict):
                if key == "main":
                    points_str += edu_custom_1.format(value)

                points_str += edu_custom_2.format(value)
            else:
                for subkey, subvalue in value.items():
                    if subkey == "main":
                        points_str += edu_custom_2.format(subvalue)
                    else:
                        points_str += edu_custom_3.format(subvalue)

        education_str += EDU_TEMPL.format(
            degree=education["degree"],
            institution=education["institution"],
            location=education["location"],
            date=education["date"],
            content=points_str
        )

    return education_str


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
        content = section[3](recipe)
        with open(f"build/resume/{section[0]}.tex", "w") as out_file:
            out_file.write(SECTION_TEMPL.format(
                section_name=section[1],
                section_type=section[2],
                content=content
            ))

    subprocess.run(["xelatex", "resume.tex"], cwd="./build")

if __name__ == "__main__":
    main()
