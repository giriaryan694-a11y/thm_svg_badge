# THM SVG Badge Generator

A simple CLI tool to generate custom TryHackMe profile badges in SVG and PNG formats.

## Features

* Fetch public TryHackMe profile statistics
* Generate SVG and PNG badges
* Embed the profile avatar in the badge
* Save the profile picture separately
* Interactive username and output directory prompts
* Colorful terminal interface with PyFiglet and Termcolor

## Preview

<!-- Add a screenshot of your generated badge here -->

## Requirements

* Python 3.10+
* Playwright
* Chromium browser

## Installation

Clone the repository:

```bash
git clone https://github.com/giriaryan694-a11y/thm_svg_badge.git
cd thm_svg_badge
```

Install the dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

Run the script interactively:

```bash
python thm_svg_badge.py
```

Enter your TryHackMe username and output directory when prompted.

### Command-line arguments

Generate a badge for a specific username:

```bash
python thm_svg_badge.py --username YOUR_USERNAME
```

Choose an output directory:

```bash
python thm_svg_badge.py --username YOUR_USERNAME --output-dir ./badges
```

Specify a custom SVG filename:

```bash
python thm_svg_badge.py \
  --username YOUR_USERNAME \
  --output-dir ./badges \
  --output my_badge.svg
```

If no output directory is provided, the generated files are saved in the current directory.

## Output

The generator creates:

* `thm_badge.svg` - SVG badge
* `thm_badge.png` - PNG badge
* `profile_pic.*` - Downloaded profile avatar, when available

Filenames may vary depending on the options provided.

## Dependencies

* [Playwright](https://playwright.dev/python/)
* [PyFiglet](https://pypi.org/project/pyfiglet/)
* [Termcolor](https://pypi.org/project/termcolor/)

## Disclaimer

This project uses publicly accessible TryHackMe profile data. It is an independent community project and is not affiliated with or endorsed by TryHackMe.

## Author

**Aryan Giri**

GitHub: [@giriaryan694-a11y](https://github.com/giriaryan694-a11y)
