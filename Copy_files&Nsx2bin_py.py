# -*- coding: utf-8 -*-
"""
Created on Mon May 29 18:21:40 2023

First copy your files from dirf to dir2, then convert Nsx files into binary .bin for Kilosort. 32ch or 64ch are fine.
Will split the other channels like for sync or other external signal_on or anything else, into another file.
So far the Esync npy file is directly the sync timestamps. Better to check with the .nev ones.

Will do DLC analysis of copied videos. So run this script in DLC env & check if the interpreter is in the right dir.

Mind that brpylib.py has very annoying changes among versions. You should use directly copied one from this env.

@author: Junhao Huang
"""
'''
行吧那就再多写点中文注释。我真的不喜欢写中文注释。

用这个脚本，务必copy本机DEEPLABCUT环境下的brpylib.py。他们的微小版本改动会改变文件的格式/形状，这是不能随便的问题！！！

mice 我个人的实验文件编号习惯是 鼠编号-日期-实验.suffix，这里只是作为一种搜寻标记
dirf/2/ks 你要把你的文件从哪copy过来，copy到哪去，其中要从.ns6转换成.bin的文件要丢去哪（其实就是SSD盘里的KStemp，跑完KS之后没问题了丢回HDD一起做后续分析。）
mark 另一个搜寻标记，适用于日常screeniing，你只需要复制今天screen的文件，没必要把之前的全重新复制一遍，对吧？
config_path 直接copy的DLC官方代码，注意改成你自己的模型的目录
目前还是日常拔插硬盘的文件传输方式，等以后连上快速网络了再改一版网络脚本。

然后说一下几个block。
首先是日常的copy文件，以及对其中的.avi执行DLC analyse video。copy会探测文件是否存在，不复制已经存在的文件。
也是因为我的个人习惯，路径通常是  鼠编号/实验文件名（编号-日期-实验）/files，所以会在HDD上按这个规则生成路径。
这个根据各人自己习惯，学一下Path怎么玩，改成自己喜欢的就好。

第二个block是.ns6 2 .bin。如果你那天的所有鼠都只是跑了一遍screen，或者你的实验都是single session的，直接run。
会根据你的文件通道数判断是什么情况，32ch或者64ch，有无sync_ch，有无额外e_signal，比如我用的激光。
同步信号在这里会被拆分成一个单独的文件。

第三个是打开个文件对话框，让你选你要转换哪个文件。

最后那个是多session的.ns6文件拼接后转换成.bin。会重复打开一个文件选择对话框，把你要拼接的.ns6文件按  正确的顺序  选上，在最后一次出现的对话框里点取消。
为什么不简单点askopenfilenames？那玩意儿不认你的选择顺序。

目前还有个没弄的是，多sessions不会被copy到同一个目录下，目前暂时是手动挪，毕竟每个人实验文件命名习惯并不统一。

20231113 updated to local net version.

'''
import deeplabcut
import brpylib, time, datetime, shutil, numpy as np
from pathlib import Path
from matplotlib import pyplot as plt
from tkinter import filedialog
from NCP import concate_efiles


# mice = ['2309', '2310', '2311','2312']
mice = ['2311','2312']
dirfe = Path(r'Z:\HJHDATA')
dirfv = Path(r'Z:\Bonsai')
# dirfe = Path(r'J:\HJHDATA')
# dirfv = dirfe
dir2 = Path(r'H:\Filez\HJH')
dirks = Path(r'F:\KiloSortTemp')#since phy2 runs faster on SSD, we shall firstly run it on SSD and move files to HDD after curation.
mark = '*1130*'# any mark would do as long as it is in filename. For me mostly it is the date of recording. Easy-go especially for daily screening.
config_path = r'H:\Filez\HJH\DLC\HPC_DR-HJH-2023-06-04\config.yaml'



# ----------------------------------------------------------------------------
#    LOTS OF THINGS TO BE DONE.
# ----------------------------------------------------------------------------

# multi sessions, the rule of dir to store and use them

# integrate DLC in the process for daily screening. Again, what about multi-ses.
# if so, need to be run in DLC env.
# reminders of kernel change.
# ---------------------------------------------------------------------------


#%    copy files from mobile drive 2 HDD. 新鼠目前要自己手动建立新文件夹。
for m in mice:
    for i in (dirfe).rglob(m+mark):
        if 'dr' in i.name:
            if (dir2/m/i.name[:12]).exists() == 0:
                (dir2/m/i.name[:12]).mkdir()
            if (dir2/m/i.name[:12]/i.name).exists() == 0:
                shutil.copy2(i, (dir2/m/i.name[:12]/i.name))
                print(str(i), ' copied to ', str(dir2/m/i.name[:12]/i.name)) 
        else:
            if (dir2/m/i.name[:-4]).exists() == 0:
                (dir2/m/i.name[:-4]).mkdir()
            if (dir2/m/i.name[:-4]/i.name).exists() == 0:
                shutil.copy2(i, (dir2/m/i.name[:-4]/i.name))
                print(str(i), ' copied to ', str(dir2/m/i.name[:-4]/i.name))
                
    for i in (dirfv).rglob(m+mark):
        if 'dr' in i.name:
            if (dir2/m/i.name[:12]).exists() == 0:
                (dir2/m/i.name[:12]).mkdir()
            if (dir2/m/i.name[:12]/i.name).exists() == 0:
                shutil.copy2(i, (dir2/m/i.name[:12]/i.name))
                print(str(i), ' copied to ', str(dir2/m/i.name[:12]/i.name))
                if 'avi' in i.name:
                    deeplabcut.analyze_videos(config_path, videos=str(dir2/m/i.name[:12]/i.name), videotype='avi', save_as_csv=False)
                    deeplabcut.filterpredictions(config_path, str(dir2/m/i.name[:12]/i.name))    
        else:
            if (dir2/m/i.name[:-4]).exists() == 0:
                (dir2/m/i.name[:-4]).mkdir()
            if (dir2/m/i.name[:-4]/i.name).exists() == 0:
                shutil.copy2(i, (dir2/m/i.name[:-4]/i.name))
                print(str(i), ' copied to ', str(dir2/m/i.name[:-4]/i.name))
                if 'avi' in i.name:
                    deeplabcut.analyze_videos(config_path, videos=str(dir2/m/i.name[:-4]/i.name), videotype='avi', save_as_csv=False)
                    deeplabcut.filterpredictions(config_path, str(dir2/m/i.name[:-4]/i.name))

#%% multi sessions to load, concatenate, and then convert into a single .bin file.
concate_efiles(dir2)
#%%   Nsx to .bin with single sessions. For screening.
for m in mice:
    for i in (dir2/m).rglob(mark+'.ns6'):
        fn = i.name
        nsx = brpylib.NsxFile(str(i))
        data = nsx.getdata()
        # timestamp_start = data['data_headers'][0]['Timestamp']
        data = data['data'][0]
        data = data.T#this is the right order...tested with signal simulator, check by KS2.5 GUI & Nplay playback.
        nsx.close()
        sync_other = 0
             
        if data.shape[1] > 32 and data.shape[1] < 64:#32ch with 1 or 2 ch of sync or else.
            sync_other = data[:,32:]
            data = data[:,:32]
        elif data.shape[1] > 64:#64ch with, like sync sig & signal shutter.
            sync_other = data[:,64:]
            data = data[:,:64]
        elif data.shape[1] == 32:
             print('is it a 32ch file without sync?')
        elif data.shape[1] == 64:
             print('is it a 64ch file without sync?')
        else:
             print('R U sure the file is alright???')
             
             
        if (dirks/fn[:-4]).exists() == 1:
             print('target dir exists.')
        else:
             (dirks/fn[:-4]).mkdir()#generate a new dir for kilosort.
        if sync_other is not 0:
            sync = np.where(sync_other[:,0] > 4000, 1,0)# mind the amp of sync sig. 4000 is arbituary.
            sync2 = sync[1:]-sync[:-1]
            sync3 = np.where(sync2 == 1)[0]
            np.save((dir2/m/fn[:-4]/('Esync_timestamps_'+fn[:-4]+'.npy')), sync3)
            print(str(dir2/m/fn[:-4]/('Esync_timestamps_'+fn[:-4]+'.npy')), 'with shape of', str(np.shape(sync3)),' is converted')
            # Why sometimes the esync file will be deleted after KS&phy??? what is the rule??
            # however, I will convert and directly put esync file in HDD instead of stay around .bin in SSD.

                      
        data = np.ascontiguousarray(data)# before this, it is F_contiguous and errors will pop out. Then it is C.
        # fb = (dirks/fn[:-4])/(fn[:-4]+'_'+str(timestamp_start)+'.bin')
        fb = (dirks/fn[:-4])/(fn[:-4]+'.bin')
        if fb.exists() == 1:
             print('converted file exists. Please check.')
        else:
             fb.write_bytes(data)
        print(str(dir2/m/fn), ', with shape', str(np.shape(data)), ', ', 'is converted.')
#%% After sorting, change python interpreter and start phy2 here.
from phy.apps.template import template_gui
fn = 'TR141_20231123'
template_gui('F:KilosortTemp\\'+fn+'\\params.py')

            
#%% choose a single file to convert and save in SSD
dir2 = r'J:\Eletrophysiology'
fdir = Path(filedialog.askopenfilename(initialdir=dir2))

nsx = brpylib.NsxFile(str(fdir))
data = nsx.getdata()
timestamp_start = data['data_headers'][0]['Timestamp']
data = data['data'][0]
data = data.T#this is the right order...tested with signal simulator, check by KS2.5 GUI & Nplay playback.
nsx.close()
sync_other = 0
if data.shape[1] > 32 and data.shape[1] < 64:#32ch with 1 or 2 ch of sync or else.
    sync_other = data[:,32:]
    data = data[:,:32]
elif data.shape[1] > 64:#64ch with, like sync sig & laser_on signal
    sync_other = data[:,64:]
    data = data[:,:64] 
elif data.shape[1] == 32:
     print('is it a 32ch file without sync?')
elif data.shape[1] == 64:
     print('is it a 64ch file without sync?')
else:
     print('R U sure the file is alright???')                
data = np.ascontiguousarray(data)# before this, it is F_contiguous and errors will pop out. Then it is C.


if (dirks/fdir.name[:-4]).exists() == 1:
    pass
else:
    (dirks/fdir.name[:-4]).mkdir()
fb = dirks/fdir.name[:-4]/(fdir.name[:-4]+'.bin')# need to mkdir before
if fb.exists() == 1:
    print('converted file exists. Please check.')
else:
      fb.write_bytes(data)
      
      
      #bugs here!
if sync_other is not 0:
    sync = np.where(sync_other[:,0] > 4000, 1,0)# mind the amp of sync sig. 4000 is arbituary.
    sync2 = sync[1:]-sync[:-1]
    sync3 = np.where(sync2 == 1)[0]
    np.save((fdir.parents/('Esync_timestamps_'+fdir.name[:-4]+'.npy')), sync3)#bug here!!!
    np.save((fdir.name[:-4]+'Esync_timestamps_.npy'), sync3)









