#/usr/lib/python3
import setuptools

long_dsc = ''
with open('README.md', 'r') as file_obj:
    long_dsc = file_obj.read()

setuptools.setup(
    name='llamas',
    version='0.1',
    author='Zach Volchak',
    author_email='zakhar.volchak@hpe.com',
    description='An event subscribtion Redfish rough emulator.',
    long_description=long_dsc,
    long_description_content_type='text/markdown',
    url='https://github.hpe.com/atsugami-kun/flask-api-template',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX :: Linux',
    ],
)