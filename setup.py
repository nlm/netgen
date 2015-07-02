from setuptools import setup,find_packages

setup(
    name = "netgen",
    version = "0.3.0",
    packages = ['netgen'],
    author = "Nicolas Limage",
    description = "a templated ip address plan generator",
    license = "GPL",
    keywords = "ip range network space",
    url = "https://github.com/nlm/netgen",
    classifiers = [
        'Development Status :: 4 - Beta',
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
        'six',
    ],
    entry_points = {
        'console_scripts': [
            'network-generator = netgen.main:main',
            'netgen = netgen.main:main',
        ],
    },
    test_suite = 'netgen.test',
)
