from setuptools import setup, find_packages

requirements = [
    "requests",
    "websocket-client==1.3.1", 
    "setuptools", 
    "json_minify", 
    "six",
    "aiohttp",
    "websockets"
]

with open("README.md", "r") as stream:
    long_description = stream.read()

setup(
    name="amino.fix",
    license="MIT",
    author="Minori",
    version="2.3.6.1",
    author_email="minorigithub@gmail.com",
    description="Library for Amino. Discord - https://discord.gg/Bf3dpBRJHj",
    url="https://github.com/Minori100/Amino.fix",
    packages=find_packages(),
    long_description=long_description,
    install_requires=requirements,
    keywords=[
        'aminoapps',
        'amino.fix',
        'amino',
        'amino-bot',
        'narvii',
        'api',
        'python',
        'python3',
        'python3.x',
        'minori'
    ],
    python_requires='>=3.6',
)
