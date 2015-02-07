from setuptools import setup

setup(
    name = "seekguidance",
    version = "0",
    description = "Generate random Dark Souls 1/2 messages",
    url = "https://github.com/ahihi/seekguidance",
    author = "Miranda Kastemaa",
    author_email = "miranda@foldplop.com",
    license = "cc0",
    packages = ["seekguidance"],
    scripts = ["bin/seekguidance"],
    install_requires = [],
    zip_safe = False,
    include_package_data = True,
)