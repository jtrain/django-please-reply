from setuptools import setup, find_packages

setup(
    name='django-please-reply',
    version='0.1.0',
    description='track attendee replies to non-recurring events',
    long_description=open('README.rst').read(),
    author='Jervis Whitley',
    author_email='jervisw@whit.com.au',
    url='http://github.com/jtrain/django-please-reply/tree/master',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    package_data = {
    },
    zip_safe=False,
)
