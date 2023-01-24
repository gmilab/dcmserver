# Ibrahim Lab DICOM storage server
Inspired by Logi Vidarsson's perl scripts and Wayne Lee's bash scripts for dcmtk


## Install
```bash
# install dependencies
sudo add-apt-repository universe  # dcmtk lives on the universe repo
sudo apt install dcmtk python3-pip

# download repository and install python packages
git clone https://github.com/gmilab/dcmserver
cd dcmserver
pip install -U -r ./requirements.txt

# create a user for the server
sudo useradd dcmserver
```

Edit the systemd unit files with the appropriate paths and parameters, then install them.

```bash
sudo cp dicomserver.service dicomserver-mover.service /etc/systemd/system
sudo systemctl daemon-reload

sudo systemctl enable dicomserver.service
sudo systemctl enable dicomserver-mover.service

sudo systemctl start dicomserver.service
sudo systemctl start dicomserver-mover.service
```


Then test from another computer
```bash
cd [directory with dicom files]
dcmsend [server] [port] ./
```
