
import setuptools

setuptools.setup(name='tygs',
                 version='0.2.0',
                 description='New generation web framework',
                 long_description=open('README.rst').read().strip(),
                 author='Sam, Max & friends',
                 author_email='lesametlemax@gmail.com',
                 url='https://github.com/sametmax/tygs/',
                 packages=setuptools.find_packages('src'),
                 package_dir={'': 'src'},
                 install_requires=['aiohttp', 'jinja2', 'aiohttp-jinja2',
                                   'path.py'],
                 extras_require={
                     'dev': ['sphinx', 'tox', 'pytest', 'requests',
                             'pytest-cov']
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
