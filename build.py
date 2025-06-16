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
        out_file.write("\cvsection{Skills}\n\n\\begin{cvparagraph}\n\n")

        for i, section in enumerate(recipe["skills"]):
            out_file.write(f"\\textbf{{{section['name']}:}} ")

            for j, skill in enumerate(section["content"]):
                if j != 0:
                    out_file.write(", ")

                out_file.write(data["skills"][skill])

            if i < len(recipe["skills"]) - 1:
                out_file.write(" \\\\")

            out_file.write("\n")

        out_file.write("\n\end{cvparagraph}\n")


    with open("build/resume/projects.tex", "w") as out_file:
        out_file.write("\cvsection{Projects}\n\n\\begin{cventries}\n\n")
        
        for project_recipe in recipe["projects"]:
            project = data["projects"][project_recipe['name']]
            out_file.write(f"\\cventry\n{{\href{{{project['href']}}}{{{project['link']}}}}}\n")
            out_file.write(f"{{{project['title']}}}\n{{{project['date']}}}\n{{}}\n")

            out_file.write("{\n  \\begin{cvitems}\n")

            out_file.write("    \\item {\\textbf{Technologies:} " + project['tech'] + "}\n")

            for key, value in project["points"].items():
                if key not in project_recipe["exclude"]:
                    out_file.write(f"    \\item {{{value}}}\n")

            out_file.write("  \\end{cvitems}\n}\n\n")

        out_file.write("\end{cventries}\n")


    with open("build/resume/experience.tex", "w") as out_file:
        out_file.write("\cvsection{Work Experience}\n\n\\begin{cventries}\n\n")

        for experience_recipe in recipe["experience"]:
            experience = data["experience"][experience_recipe["name"]]
            title = experience[experience_recipe["title"]]

            out_file.write(f"  \\cventry\n    {{{title}}}\n    {{{experience['employer']}}}\n    {{}}\n    {{{experience['date']}}}\n"
                          + "    {\n      \\begin{cvitems}")
            
            for key, value in experience["points"].items():
                if key not in experience_recipe["exclude"]:
                    if isinstance(value, dict):
                        for subval in value.values():
                            out_file.write("\n        \hspace{1mm} \\bullet \hspace{1mm} {"
                                        + subval + "} \\newline")
                    else:
                        out_file.write("\n        \item {" + value + "} \\newline")

            out_file.write("\n      \end{cvitems}\n    }\n\n")

        out_file.write("\end{cventries}\n")

    
    with open("build/resume/education.tex", "w") as out_file:
        out_file.write("\cvsection{Education}\n\n\\begin{cventries}\n")
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

            out_file.write(EDU_TEMPL.format(
                education["degree"],
                education["institution"],
                education["location"],
                education["date"],
                points_str
            ))

        out_file.write("\n\\end{cventries}\n")

    subprocess.run(["xelatex", "resume.tex"], cwd="./build")

if __name__ == "__main__":
    main()
