import sys
import json
import os
import shutil
import subprocess
from pathlib import Path

SECTION_NAMES = [
    "summary",
    "skills",
    "projects",
    "experience",
    "education"
]

RESUME_TEMPL = Path("templates/resume-template.txt").read_text()
SECTION_TEMPL = Path("templates/section-template.txt").read_text()
PROJECT_TEMPL = Path("templates/project-template.txt").read_text()
EXP_TEMPL = Path("templates/experience-template.txt").read_text()

EDU_TEMPL = """\
\cventry
  {{{0}}} % Degree
  {{{1}}} % Institution
    {{{2}}} % Location
    {{{3}}} % Date(s)
    {{
      \\begin{{cvitems}} % Description(s) bullet points{4}      
      \\end{{cvitems}}
    }}
"""

IMPORT_TOKEN = "\input{{resume/{name}.tex}}\n"
BOLD_ITEM_TOKEN = "\\textbf{{{skill_category}}}: {content}"
BOLD_ITEM_NEWLINE_TOKEN = f"{BOLD_ITEM_TOKEN} \\\\\n"
BULLET_ITEM_TOKEN = "\\item {{{item}}}"
INDENTED_BULLET_ITEM_TOKEN = "\hspace{{1mm}} \\bullet \hspace{{1mm}} {item} \\newline"

edu_std_point = "\n        \item {{{0}}}"
edu_custom_1 = "\n         {0} \\newline"
edu_custom_2 = "\n         \hspace{{1mm}} \\bullet \hspace{{1mm}} {0} \\newline"
edu_custom_3 = "\n         \hspace{{5mm}} \\bullet \hspace{{1mm}} {0} \\newline"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build.py recipe")
        return
    
    recipe_name = sys.argv[1]

    with open("data.json") as file:
        data = json.load(file)

    with open("recipes.json") as file:
        recipes = json.load(file)

    recipe = recipes[recipe_name]

    shutil.rmtree("build", ignore_errors=True)
    os.makedirs("build/resume", exist_ok=True)
    shutil.copyfile("templates/awesome-cv.cls", "build/awesome-cv.cls")

    with open("build/resume.tex", "w") as out_file:
        content = ""

        for section in SECTION_NAMES:
            if recipe[section]:
                content += IMPORT_TOKEN.format(name=section)
        
        out_file.write(RESUME_TEMPL.format(content=content))

    if recipe["summary"]:
        with open("build/resume/summary.tex", "w") as out_file:
            out_file.write(SECTION_TEMPL.format(
                section_name="Objective",
                section_type="cvparagraph",
                content=data["summaries"][recipe["summary"]])
            )


    with open("build/resume/skills.tex", "w") as out_file:
        skills_str = ""
        for i, section in enumerate(recipe["skills"]):
            curr_skill_str = ""

            for j, skill in enumerate(section["content"]):
                if j != 0:
                    curr_skill_str += ", "

                curr_skill_str += data["skills"][skill]

            token = BOLD_ITEM_NEWLINE_TOKEN \
                if i != len(recipe["skills"]) - 1 \
                else BOLD_ITEM_TOKEN

            skills_str += token.format(
                skill_category=section["name"],
                content=curr_skill_str
            )

        out_file.write(SECTION_TEMPL.format(
            section_name="Skills",
            section_type="cvparagraph",
            content=skills_str
        ))

    with open("build/resume/projects.tex", "w") as out_file:
        projects_str = ""
        
        for project_recipe in recipe["projects"]:
            project = data["projects"][project_recipe['name']]
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

        out_file.write(SECTION_TEMPL.format(
            section_name="Projects",
            section_type="cventries",
            content=projects_str
        ))


    with open("build/resume/experience.tex", "w") as out_file:
        exp_str = ""
        for experience_recipe in recipe["experience"]:
            experience = data["experience"][experience_recipe["name"]]
            curr_exp_str = ""
            
            for key, value in experience["points"].items():
                if key not in experience_recipe["exclude"]:
                    if isinstance(value, dict):
                        for subval in value.values():
                            curr_exp_str += INDENTED_BULLET_ITEM_TOKEN.format(item=subval)
                    else:
                        curr_exp_str += BULLET_ITEM_TOKEN.format(item=value) + "\\\\newline"

            exp_str += EXP_TEMPL.format(
                name=experience["name"],
                employer=experience["employer"],
                date=experience["date"],
                content=curr_exp_str
            )

        out_file.write(SECTION_TEMPL.format(
            section_name="Experience",
            section_type="cventries",
            content=exp_str
        ))

    
    with open("build/resume/education.tex", "w") as out_file:
        for education_recipe in recipe["education"]:
            education = data["education"][education_recipe["name"]]

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

            out_file.write(
                SECTION_TEMPL.format(
                    section_name="Education",
                    section_type="cventries",
                    content=EDU_TEMPL.format(
                        education["degree"],
                        education["institution"],
                        education["location"],
                        education["date"],
                        points_str
                    )
                )
            )

    subprocess.run(["xelatex", "resume.tex"], cwd="./build")

if __name__ == "__main__":
    main()
