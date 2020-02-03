#/usr/lib/python3
import setuptools

long_dsc = ''
with open('README.md', 'r') as file_obj:
    long_dsc = file_obj.read()


# Get dependencies from the requirements.txt and set it to install_requires prop.
#This will help resolve dependencies recursively when this package added as such
#by outside world.
requirements = []
with open('requirements.txt', 'r') as file_obj:
    requirements = file_obj.read().split('\n')

setuptools.setup(
    name='llamas',
    version='0.1',
    license='GPLv2',
    author='Zach Volchak',
    author_email='zakhar.volchak@hpe.com',
    description='An event subscribtion Redfish rough emulator.',
    long_description=long_dsc,
    long_description_content_type='text/markdown',
    url='https://github.hpe.com/atsugami-kun/flask-api-template',
    packages=setuptools.find_packages(),
    package_data = {
        # include none .py project artifacts (e.g. cfg files)
        '': ['config', '*.config', '*.cfg'],
    },

    install_requires=requirements,

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX :: Linux',
    ],
)