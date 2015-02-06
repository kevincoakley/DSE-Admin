#!/bin/bash
# Tested on Ubuntu 14.04

# APT-GET Software Install
/usr/bin/sudo /usr/bin/apt-get update
/usr/bin/sudo /usr/bin/apt-get upgrade -y
/usr/bin/sudo /usr/bin/apt-get install git build-essential firefox -y
/usr/bin/sudo /usr/bin/apt-get install alex cabal-install emacs gfortran ghc ghc-haddock happy html2text jed m17n-contrib m17n-db m4 mercurial mysql-common r-base-dev s3cmd slsh unzip zip -y

# Install Anaconda
/usr/bin/wget -P /tmp/ http://repo.continuum.io/archive/Anaconda-2.1.0-Linux-x86_64.sh
/bin/bash /tmp/Anaconda-2.1.0-Linux-x86_64.sh -b
/bin/echo "export PATH=\"/home/ubuntu/anaconda/bin:\$PATH\"" >> /home/ubuntu/.bashrc
source /home/ubuntu/.bashrc
/home/ubuntu/anaconda/bin/conda update conda --yes
/home/ubuntu/anaconda/bin/conda update anaconda --yes
/home/ubuntu/anaconda/bin/conda update ipython --yes

# Install Conda Packages
/home/ubuntu/anaconda/bin/conda install scrapy --yes
/home/ubuntu/anaconda/bin/conda install apptools --yes
/home/ubuntu/anaconda/bin/conda install basemap --yes
/home/ubuntu/anaconda/bin/conda install biopython --yes
/home/ubuntu/anaconda/bin/conda install cubes --yes
/home/ubuntu/anaconda/bin/conda install disco --yes
/home/ubuntu/anaconda/bin/conda install envisage --yes
/home/ubuntu/anaconda/bin/conda install gevent_zeromq --yes
/home/ubuntu/anaconda/bin/conda install keyring --yes
/home/ubuntu/anaconda/bin/conda install launcher --yes
/home/ubuntu/anaconda/bin/conda install libnetcdf --yes
/home/ubuntu/anaconda/bin/conda install mathjax --yes
/home/ubuntu/anaconda/bin/conda install mayavi --yes
/home/ubuntu/anaconda/bin/conda install mdp --yes
/home/ubuntu/anaconda/bin/conda install netcdf4 --yes
/home/ubuntu/anaconda/bin/conda install opencv --yes
/home/ubuntu/anaconda/bin/conda install pykit --yes
/home/ubuntu/anaconda/bin/conda install pysal --yes
/home/ubuntu/anaconda/bin/conda install pysam --yes
/home/ubuntu/anaconda/bin/conda install pyside --yes
/home/ubuntu/anaconda/bin/conda install pyzmq --yes
/home/ubuntu/anaconda/bin/conda install imaging —-yes
/home/ubuntu/anaconda/bin/conda install paramiko --yes

# Install PIP Packages
/home/ubuntu/anaconda/bin/pip install graphviz
/home/ubuntu/anaconda/bin/pip install list
/home/ubuntu/anaconda/bin/pip install mrjob
/home/ubuntu/anaconda/bin/pip install plotly
#/home/ubuntu/anaconda/bin/pip install orange # Takes about 20 minutes to install
/home/ubuntu/anaconda/bin/pip install sparsesvd
/home/ubuntu/anaconda/bin/pip install rpy2

# Install Packages that don't must be manually installed

# pyrsvd
/usr/bin/wget -P /tmp/ https://pyrsvd.googlecode.com/files/pyrsvd-0.2.5.tar.gz
/bin/mkdir /tmp/pyrsvd
/bin/tar zxf /tmp/pyrsvd-0.2.5.tar.gz -C /tmp/pyrsvd
cd /tmp/pyrsvd
/home/ubuntu/anaconda/bin/python /tmp/pyrsvd/setup.py install
cd ~

# Configure iPython Notebook Server
/usr/bin/wget -P /tmp/ https://s3.amazonaws.com/mas-dse-ami/ipythonconf.tar.gz
/bin/tar zxf /tmp/ipythonconf.tar.gz -C /home/ubuntu/

# Check out and link the Class GitHub Repositories
/usr/bin/git clone https://github.com/mas-dse/DSE200.git ~/DSE200
/usr/bin/git clone https://github.com/mas-dse/DSE200-notebooks.git ~/DSE200-notebooks
/bin/ln -s ~/DSE200/data/ ~/data
/bin/ln -s ~/DSE200/AWS_scripts/ ~/scripts
/bin/ln -s ~/DSE200-notebooks/ ~/notebooks

# Update the DSE200 and DSE200-notebooks repositories at boot
/bin/cat <<EOF | /usr/bin/sudo /usr/bin/tee /etc/rc.local
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.
su ubuntu -c "cd /home/ubuntu/DSE200; git pull"
su ubuntu -c "cd /home/ubuntu/DSE200-notebooks; git pull"

exit 0
EOF
