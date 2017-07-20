from setuptools import setup,find_packages

setup(
    name = "netgen",
    version = "0.5.0-beta1",
    packages = find_packages(),
    author = "Nicolas Limage",
    author_email = 'github@xephon.org',
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
            'netgen-stats = netgen.stats:main',
            'netgen-yaml2json = netgen.converters:yaml2json',
            'netgen-json2yaml = netgen.converters:json2yaml',
        ],
    },
    include_package_data = True,
    package_data = {
        'netgen': ['templates/*.tpl'],
    },
    test_suite = 'test_netgen',
)
