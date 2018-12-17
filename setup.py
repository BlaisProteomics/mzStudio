from setuptools import setup, find_packages



setup(name = 'mzStudio',
      version = '1.2',
      author = 'Scott Ficarro, William Max Alexander',
      author_email = 'Scott_Ficarro@dfci.harvard.edu',
      packages = ['mzStudio'],
      package_data = {'mzStudio' : ['mzStudio/image/*',
                                    'mzStudio/settings/*']},
      include_package_data = True,
      url = 'http://github.com/BlaisProteomics/mzStudio',
      description = 'Mass Spectrometry/Proteomics Data Analysis Application',
      install_requires = ['multiplierz']
      )