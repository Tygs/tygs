
import setuptools


def get_requirements(path):

    setuppy_pattern = \
        'https://github.com/{user}/{repo}/tarball/master#egg={egg}'

    dependency_links = []
    install_requires = []
    with open(path) as f:
        for line in f:

            if line.startswith('-e'):
                url_infos = re.search(
                    r'github.com/(?P<user>[^/.]+)/(?P<repo>[^.]+).git#egg=(?P<egg>.+)',
                    line).groupdict()
                dependency_links.append(setuppy_pattern.format(**url_infos))
                egg_name = '=='.join(url_infos['egg'].rsplit('-', 1))
                install_requires.append(egg_name)
            else:
                install_requires.append(line.strip())

    return install_requires, dependency_links


requirements, dependency_links = get_requirements('requirements.txt')
dev_requirements, dependency_links = get_requirements('dev-requirements.txt')

setuptools.setup(name='tygs',
                 version='0.2.0',
                 description='New generation web framework',
                 long_description=open('README.rst').read().strip(),
                 author='Sam, Max & friends',
                 author_email='lesametlemax@gmail.com',
                 url='https://github.com/sametmax/tygs/',
                 packages=setuptools.find_packages('src'),
                 package_dir={'': 'src'},
                 install_requires=requirements,
                 extras_require={
                     'dev': dev_requirements
                 },
                 include_package_data=True,
                 license='WTFPL',
                 zip_safe=False,
                 keywords='tygs async rpc pubsub http websocket',
                 classifiers=['Development Status :: 1 - Planning',
                              'Intended Audience :: Developers',
                              'Natural Language :: English',
                              'Programming Language :: Python :: 3.5',
                              'Programming Language :: Python :: 3 :: Only',
                              'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
                              'Topic :: Internet :: WWW/HTTP :: Site '
                              'Management',
                              'Operating System :: OS Independent'],)
