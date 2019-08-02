import setuptools
from pathlib import Path


def get_version():
    version_str = (Path(__file__).parent / 'tbparser/version.py').read_text()
    exec(version_str)
    try:
        version = str(locals()['__version__'])
    except KeyError:
        version = '0.0.0'
    return version


long_description = (Path(__file__).parent / 'README.md').read_text()

setuptools.setup(
    name='tbparser',
    version=get_version(),
    author='Vadim Velicodnii',
    author_email='vadim@velikodniy.name',
    description='Parse tensorboard logs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/velikodniy/tbparser',
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'numpy>1.15.4',
        'imageio>=2.5.0',
        'tensorboard>=1.13.1',
        'crc32c>=1.7',
    ],
    tests_require=[
        'pytest>=4.4.1'
    ],
    setup_requires=[
        'pytest-runner>=4.4',
    ],
    python_requires='>=3.6, <4',
)
