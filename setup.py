from setuptools import setup,find_packages

setup(
    name = "netgen",
    version = "0.0.1",
    packages = find_packages(),
    author = "Nicolas Limage",
    description = "a ip address plan generator",
    license = "GPL",
    keywords = "ip range network space",
    url = "https://github.com/nlm/firval",
    classifiers = [
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
    ],
    install_requires = [
        'Jinja2',
        'PyYAML',
        'voluptuous>=0.8.0',
        'ipaddress',
    ],
    entry_points = {
        'console_scripts': [
            'network-generator = netgen.main:main',
        ],
    },
)
