---
title: Mirai Machine
date: 2023-08-01
tags: [ctf,htb]
---

Someone told me Mirai is an easy machine, so I decided to try it out.

Sometimes do easy stuff, like you killed bots in CSGO 

Mirai was a botnet that essentially tried to crack down on devices using default passwords. 

Now all CTF writeup are very coherant, that is never the case with me (I should play more CTFs)
So, I will just write it like a not so easy to replicate guide so that all the fun is not lost. 

## Running NMAP 

Run a nmap and find some ports (ssh,tcp,http)

![alt text](/static/assets/mirai_htb_nmap.png)

We do get a debian version, it is advisable to look if something wrong with it, but the path integral of thoughts of my brain is inclined to look around more so that I find a more familiar something. 


## Do some gobuster 

Doing some gobuster reveals ```\admin``` . Navigating there you get a pihole admin page. 
Now , where do you find a pihole I wonder. 
I am embarassed that I realised it way later than I was supposed to. 

### Realise it runs on raspberrypi
#### Realise it is 'Mirai' botnet, so try default passwords 
###### It again took me longer to realise than that it should have

Just ssh after that and you see a ```user.txt```. cat it and get a user flag. 

![alt text](/static/assets/mirai_htb_userflag.png)


### But 
#### But
##### But

You cannot call it a day here, because if you stop now, you won't continue it , ever, so I decided to do the root flag and give myself an excuse to binge entire solo levelling for the 10th time again. 

## Find the root flag 

You caveman rawdog the find command with keywords like root, flag

And you find it by 

`sudo find / "*root*" | grep root.txt`

And you get these 


```
/lib/live/mount/persistence/sda2/root/root.txt
/root/root.txt
```

Which one I choose to check out is obvious 

But you cannot just read the root.txt, 

`ls: cannot open directory root/: Permission denied`

I am not proud of the fact my first thought was to look at those Debian version exploits here, some linpeas? 

I just had to `su -` 
(if you didn't realise that instinticively, interesting)

```
root@raspberrypi:~# cat root.txt 
I lost my original root.txt! I think I may have a backup on my USB stick...
```

Looks like I will have to explore the other mount point that came out of find command. 

```
root@raspberrypi:/lib/live/mount/persistence/sda2/root# ls
root.txt
root@raspberrypi:/lib/live/mount/persistence/sda2/root# cat root.txt 
I lost my original root.txt! I think I may have a backup on my USB stick...
```

well , USB == lsblk 

```
root@raspberrypi:~# lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda      8:0    0   10G  0 disk 
├─sda1   8:1    0  1.3G  0 part /lib/live/mount/persistence/sda1
└─sda2   8:2    0  8.7G  0 part /lib/live/mount/persistence/sda2
sdb      8:16   0   10M  0 disk /media/usbstick
sr0     11:0    1 1024M  0 rom  
loop0    7:0    0  1.2G  1 loop /lib/live/mount/rootfs/filesystem.squashfs
```

there is a usbstick 

```
root@raspberrypi:/media/usbstick# ls
damnit.txt  lost+found
root@raspberrypi:/media/usbstick# cat damnit.txt 
Damnit! Sorry man I accidentally deleted your files off the USB stick.
Do you know if there is any way to get them back?

-James
```

At this point , I turned to some blogs. (uhm chatgpt)
Again, I skimmed so that I don't get the full answer. 
I saw "strings"

I ran the command wherever I thought it was relevant (to me, which is not an objective metric for relevance, nor is a wise way, take a minute or two to think where you should run it and you should have your answer)

```
root@raspberrypi:/media/usbstick# strings /dev/sdb
\F\f\F\f
>r &
/media/usbstick
lost+found
root.txt
damnit.txt
>r &
>r &
/media/usbstick
lost+found
root.txt
damnit.txt
>r &
/media/usbstick
2]8^
lost+found
root.txt
damnit.txt
>r &
3d3e483143ff12ec505d026fa13e020b
Damnit! Sorry man I accidentally deleted your files off the USB stick.
Do you know if there is any way to get them back?
-James

```

There is a weird string
That was the flag 

The End