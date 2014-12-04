

from setuptools import setup


setup(
    name='Tygs',
    version='0.1',
    author='Sam et Max',
    author_email='lesametlemax@gmail.com',
    py_modules=['tygs'],
    license='BSD Licence',
    long_description=open('README.rst').read(),
    description="Pure Python asynchronous Web framework with PUB/SUB, RPC, tasks queues and multiprocessing packed in a nice API.",
    url='http://github.com/sametmax/tygs',
    keywords="python, asynchronous, web",
    include_package_data=True,
    install_requires=['klein'],
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
)
