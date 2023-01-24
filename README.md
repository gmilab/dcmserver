# Ibrahim Lab DICOM storage server
Inspired by Logi Vidarsson's perl scripts and Wayne Lee's bash scripts for dcmtk


## Install
```
# install dependencies
sudo apt install dcmtk python3-pip
sudo useradd dcmserver

git clone https://github.com/gmilab/dcmserver
cd dcmserver
pip install -U -r ./requirements.txt
```

Edit the systemd unit files with the appropriate paths and parameters, then install them.

```
sudo cp dicomserver.service dicomserver-mover.service /etc/systemd/system
sudo systemctl daemon-reload

sudo systemctl enable dicomserver.service
sudo systemctl enable dicomserver-mover.service

sudo systemctl start dicomserver.service
sudo systemctl start dicomserver-mover.service
```


Then test from another computer
```
cd [directory with dicom files]
dcmsend [server] [port] ./
```
