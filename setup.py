import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scanplans",
    version="0.0.1",
    author="Billinge group",
    author_email="sb2896@columbia.edu",
    description="A package of bluesky plans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Billingegroup/bluesky_scanplans",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.6',
)
