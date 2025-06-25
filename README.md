# Resume Builder

I find that it is helpful to tailor my resumes to each individual job that I apply to. However, I don't want to create many similar versions of the same resume, nor do I want to overwrite my resume each time I tailor it. This repository allows me to easily manage different versions of my resume with JSON files.

Essentially, this repository uses Python as a preprocessor to generate the LaTeX source code of a resume. The LaTeX resume code is based on Posquit0's [Awesome CV](https://github.com/posquit0/Awesome-CV).

## Usage

Execute the `build.py` script with Python 3. The script takes one additional command-line argument indicating the name of the resume to build. Resume names are identical to the names of the files in the `recipes` directory, but do not include the `.json` extension. A sample invocation might look like this (on MacOS or Linux):

```sh
python3 build.py standard
```

Note that this invocation only works because `standard.json` is a file in the `recipes` directory.

The script will create a directory called `build`, which will contain a LaTeX project. Assuming that the LaTeX compilation was successful, the resulting resume can be found at `build/resume.pdf`.

## Dependencies

This project requires both an installation of Python 3 and an installation of LaTeX.

- Python 3 can be installed from [Python.org](https://www.python.org/).
- LaTeX installations may vary by operating system. On Debian-based Linux distros, `sudo apt install texlive-full` should work just fine.

## Project Structure

In general:

- `data.json` contains components (snippets of text relating to my experience and projects) that I might want to include in a resume.
- Each JSON file in the `recipes` directory defines a unique resume by specifying which components should be included.

If I'm editing the quality of writing in my resume or adding new skills/projects, then I'll make changes to `data.json`.

If I'm tailoring a resume to a specific job, I'll either add a new file to the `recipes` directory or change an existing file.
