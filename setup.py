from setuptools import setup,find_packages

setup(
    name = "netgen",
    version = "0.4b5",
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
            'network-generator = netgen.__main__:main',
            'netgen = netgen.__main__:main',
        ],
    },
    include_package_data = True,
    package_data = {
        'supgen': ['templates/*'],
    },
    test_suite = 'test_netgen',
)
