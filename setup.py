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

setup(
    name="amino.fix",
    license="MIT",
    author="Minori",
    version="2.3.6.2",
    author_email="minorigithub@gmail.com",
    description="Library for Amino. Discord - https://discord.gg/Bf3dpBRJHj",
    url="https://github.com/Minori100/Amino.fix",
    packages=find_packages(),
    long_description=open("README.md").read(),
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
