# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 15:50:28 2023

Welcome to NCP lab! The lasy authar so far has not written any informative docstring yet.

@author: Junhao
"""
'''
UPDATES

20230708, for 1d info & single neuron shuffle test, Skaggs info & Olypher info.

20230715. Core reconstructed, by reconstruction of time defined by external clock(Master8).
Which means all V_frames or E_timestamps are translated into time by count of sync pulse,
in other words, full trust was given to Maser8.
Pros, reconstruted time by many interpolations(Scipy, UniviariateSpline) might be easy to use.
Cons, we cannot know if Master8 is really good enough so time-related calculation might be wrong.

20231119 merged codes from Mingze. Not finished yet.
20231120 conserve experiment_tag and turn into dict for compatibility.
20231203 waveforms extraction and comparison with tagging session waveforms implemented.




'''

#%% Main Bundle


# ----------------------------------------------------------------------------
#    LOTS OF THINGS TO BE DONE.
# ----------------------------------------------------------------------------

# For new cam, introduce PC timestamps into .csv for more reference.

# later, mind if there are some nans in DLC files.
# jumpy detection, or smooth, Kalman Filter!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# everything is function of time. How to verify the result after spline-interp of xy?? make a new video?



# waveform putative IN or PCs. Then optotag, R of waveforms of units.
# in class unit, furthur work with its quality check like L-ratio and others. May need to load more files from KS&phy2.


# Master8 got a bit faster or DAQ slower? e_intervals are mostly 14998 and none greater than 15000. Errors are accumulating!!!!!!!!!!!!!!!!!!!

# better session, coorperate with behavior-tags 2 frames. 

# LFP&spike, their binding do not need anything related to videos. Well except for spd thresh, or maybe some relation with its position.
# func & methods for 2D exp. , smoothing kernels. More and More
# decoding. some bayesian?

# raster plot
# save ppt for ana of every units, for future scan?



# ----------------------------------------------------------------------------
#                  Packages 
# ----------------------------------------------------------------------------

import brpylib, time, random, pickle, numpy as np, pandas as pd, matplotlib.pyplot as plt, numpy_groupies as npg
from scipy import optimize, ndimage, interpolate, stats
from pathlib import Path
from tkinter import filedialog


# ----------------------------------------------------------------------------
#                  Functions here
# ----------------------------------------------------------------------------


def load_files(fdir, fn, Nses, experiment_tag, dlc_tail):  
    # if Nses > 1, mind the rule of name.
    spike_times = np.load(fdir/fn/'spike_times.npy')
    spike_times = np.squeeze(spike_times)# delete that stupid dimension.
    spike_clusters = np.load(fdir/fn/'spike_clusters.npy')
    clusters_quality = pd.read_csv(fdir/fn/'cluster_group.tsv', sep='\t')
    esync_timestamps_load = np.load(fdir/fn/('Esync_timestamps_'+fn+'.npy'))  

    if 'signal' in experiment_tag.keys() :
        signal_on_timestamps_load = np.load(fdir/fn/('Signal_on_timestamps_'+fn+'.npy')) 


    if Nses == 1:
        timestamps = spike_times    
        spike_clusters2 = spike_clusters
        dlch5 = pd.read_hdf(fdir/fn/(fn+dlc_tail))
        esync_timestamps = esync_timestamps_load
        dlc_files = dlch5
        frame_state = False
        if experiment_tag['video record mode'] == 'FrameState':                        # new FrameState recording mode for new cams.
            frame_state = pd.read_csv(fdir/fn/(fn+'FrameState.csv'))
            vsync_temp = np.array(frame_state['SyncLED'], dtype='uint')
        elif experiment_tag['video record mode'] == 'Bonsai':                            # for old files.
            vsync_csv = pd.read_csv(fdir/fn/(fn+'.csv'), names=[0,1,2])
            vsync_temp = np.array(vsync_csv.loc[:,1], dtype='uint')
        else:
            raise Exception('please choose the right mode for data loading.')
        vsync = (np.where((vsync_temp[1:] - vsync_temp[:-1]) ==1)[0]+1)
        if 'signal' in experiment_tag.keys():
            signal_on_timestamps = signal_on_timestamps_load
    elif Nses > 1:
        filenames = []
        file_temp = 1
        while file_temp is not str():
            file_temp = filedialog.askopenfilename(initialdir=Path(fdir/fn))
            file_temp2 = Path(file_temp)
            filenames.append(file_temp2.name[:-4])
        if filenames[-1] == str():
            filenames = filenames[:-1]
                        
        timestamps = []
        spike_clusters2 = []
        dlc_files = []
        vsync = []
        frame_state = []
        
        for i in filenames:
            dlch5 = pd.read_hdf(fdir/fn/(i+dlc_tail))
            dlc_files.append(dlch5)
            if experiment_tag['video record mode'] == 'FrameState':
                frame_state = pd.read_csv(fdir/fn/(i+'FrameState.csv'))    #Try using this rule to name files.
                vsync_temp = np.array(frame_state['SyncLED'], dtype='uint')
            elif experiment_tag['video record mode'] == 'Bonsai':
                vsync_csv = pd.read_csv(fdir/fn/(i+'.csv'), names=[0,1,2])
                vsync_temp = np.array(vsync_csv.loc[:,1], dtype='uint')
            vsync.append(np.where((vsync_temp[1:] - vsync_temp[:-1]) ==1)[0]+1)
       
        # arbituarily more than 10s interval would be made when concatenate ephys files.
        
        ses_e_end = esync_timestamps_load[np.where((esync_timestamps_load[1:] - esync_timestamps_load[:-1]) > 100000)[0]]
        ses_e_end = np.append(ses_e_end, esync_timestamps_load[-1])# last one sync needed here.
        esync_timestamps = [esync_timestamps_load[np.where(esync_timestamps_load < ses_e_end[0] + 100000)]]
        
        for i in range(1, Nses):
            esync_temp = esync_timestamps_load[np.where(esync_timestamps_load < ses_e_end[i] + 100000)]
            esync_temp = esync_temp[np.where(esync_temp > ses_e_end[i-1])]
            esync_timestamps.append(esync_temp)
        if 'signal' in experiment_tag.keys():
            signal_on_timestamps = []
            for i in range(Nses):
                signal_on_temp = signal_on_timestamps_load[np.where(signal_on_timestamps_load < esync_timestamps[i][-1])]
                signal_on_temp = signal_on_temp[np.where(signal_on_temp > esync_timestamps[i][0])]
                signal_on_timestamps.append(signal_on_temp)

        
        timestamps.append(spike_times[np.where(spike_times < ses_e_end[0] + 100000)])
        spike_clusters2.append(spike_clusters[np.where(spike_times < ses_e_end[0] + 100000)])
        for i in range(1, Nses):
            spike_temp = spike_times[np.where(spike_times < ses_e_end[i] + 100000)] 
            cluster_temp = spike_clusters[np.where(spike_times < ses_e_end[i] + 100000)]
            cluster_temp = cluster_temp[np.where(spike_temp > ses_e_end[i-1] + 100000)]
            spike_temp = spike_temp[np.where(spike_temp > ses_e_end[i-1] + 100000)]
            timestamps.append(spike_temp)
            spike_clusters2.append(cluster_temp)
        print('sessions ended at timestamps,', ses_e_end)
    else:        
        raise Exception('Nses must be a positive integer.')
        
    if 'signal' in experiment_tag.keys():
        return spike_clusters2, timestamps, clusters_quality, vsync, esync_timestamps, dlc_files, frame_state, signal_on_timestamps
    else:
        return spike_clusters2, timestamps, clusters_quality, vsync, esync_timestamps, dlc_files, frame_state
    

def sync_check(esync_timestamps, vsync, Nses, fontsize):    
    if Nses == 1:
        if np.size(vsync) != np.size(esync_timestamps):
            print('N of E&V Syncs do not Equal!!! Problems with Sync!!!')
        else:
            print('N of E&V Syncs equal. You may continue.')
            # plot for check.
            fig = plt.figure(figsize=(10,5))
            ax1 = fig.add_subplot(1,2,1)
            ax2 = fig.add_subplot(1,2,2)
            esync_inter = esync_timestamps[1:] - esync_timestamps[:-1]
            vsync_inter = vsync[1:] - vsync[:-1]
            ax1.hist(esync_inter, bins = len(set(esync_inter)))
            ax1.set_title('N samples between Esyncs', fontsize=fontsize*1.3)
            ax2.hist(vsync_inter, bins = len(set(vsync_inter)))
            ax2.set_title('N frames between Vsyncs', fontsize=fontsize*1.3)
            
    else:
        fig = plt.figure(figsize=(10,5))
        ax1 = fig.add_subplot(1,2,1)
        ax2 = fig.add_subplot(1,2,2)
        ax1.set_title('N samples between Esyncs', fontsize=fontsize*1.3)
        ax2.set_title('N frames between Vsyncs', fontsize=fontsize*1.3)
        # legend?
        for i in range(Nses):
            if np.size(vsync[i]) != np.size(esync_timestamps[i]):
                print('N of E&V Syncs do not Equal!!! Problems with Sync in ses ', str(i), '!!!')
            else:
                print('ses ', str(i),' N of E&V Syncs equal. You may continue.')
                esync_inter = esync_timestamps[i][1:] - esync_timestamps[i][:-1]
                vsync_inter = vsync[i][1:] - vsync[i][:-1]
                ax1.hist(esync_inter, bins = len(set(esync_inter)), alpha=0.2)
                ax2.hist(vsync_inter, bins = len(set(vsync_inter)), alpha=0.2)


def sync_cut_stamps2time(spike_clusters, timestamps, ses, esync_timestamps, sync_rate):
    # head&tail cut here, then transform into frame_id for spd_mask.
    spike_clusters = np.delete(spike_clusters, np.where(timestamps > esync_timestamps[-1])[0])
    spike_clusters = np.delete(spike_clusters, np.where(timestamps < esync_timestamps[0])[0])
    timestamps = np.delete(timestamps, np.where(timestamps > esync_timestamps[-1])[0])
    timestamps = np.delete(timestamps, np.where(timestamps < esync_timestamps[0])[0])
    # assign time-values from esync_timestamps
    interp_y = np.linspace(0, (np.size(esync_timestamps)-1)/sync_rate, num=np.size(esync_timestamps))
    stamps2time_interp = interpolate.UnivariateSpline(esync_timestamps, interp_y, k=1, s=0)
    spiketime = stamps2time_interp(timestamps)
    return (spike_clusters,timestamps,spiketime)
    
def apply_spd_mask_20msbin(spike_clusters, timestamps, spiketime, ses, experiment_tag, temporal_bin_length=0.02):
    # applying spd_mask means sort spikes into running and staying.
    if experiment_tag['theme'] == 'spatial':
        spiketime_bin_id = (spiketime/temporal_bin_length).astype('uint')
        spike_spd_id = ses.spd_mask[spiketime_bin_id]
        high_spd_id = np.where(spike_spd_id==1)[0]
        low_spd_id= np.where(spike_spd_id==0)[0]
            
        spike_clusters_stay = spike_clusters[low_spd_id]
        timestamps_stay = timestamps[low_spd_id]
        spiketime_stay = spiketime[low_spd_id]
        spike_clusters = spike_clusters[high_spd_id]
        timestamps = timestamps[high_spd_id]
        spiketime = spiketime[high_spd_id]
        return (spike_clusters,timestamps,spiketime, spike_clusters_stay,timestamps_stay,spiketime_stay)
    else:
        raise Exception('Only spatial related experiment data should be applied with spd mask.')
        

def signal_stamps2time(esync_timestamps, signal_on_timestamps, Nses, sync_rate):
    if Nses == 1:
        interp_y = np.linspace(0, (np.size(esync_timestamps)-1)/sync_rate, num=np.size(esync_timestamps))
        stamps2time_interp = interpolate.UnivariateSpline(esync_timestamps, interp_y, k=1, s=0)
        signal_on_time = stamps2time_interp(signal_on_timestamps)    
    else:
        signal_on_time = []
        for i in range(Nses):
            if np.size(signal_on_timestamps[i]) > 0:
                interp_y = np.linspace(0, (np.size(esync_timestamps[i])-1)/sync_rate, num=np.size(esync_timestamps[i]))
                stamps2time_interp = interpolate.UnivariateSpline(esync_timestamps[i], interp_y, k=1, s=0)
                signal_on_time.append(stamps2time_interp(signal_on_timestamps[i]))
            else:
                signal_on_time.append(np.array([]))
    return signal_on_time


def spatial_information_skaggs(timestamps, ratemap, dwell_smo):
    global_mean_rate = round(np.size(timestamps)/np.sum(dwell_smo), 4)
    spatial_info = round(np.nansum((dwell_smo/np.sum(dwell_smo)) * (ratemap/global_mean_rate) * np.log2((ratemap/global_mean_rate))), 4)
    return spatial_info, global_mean_rate

def time2hd(t, time2xy_interp):
    right = np.vstack((time2xy_interp[4](t), time2xy_interp[5](t)))
    left = np.vstack((time2xy_interp[2](t), time2xy_interp[3](t)))
    hd_vector = right - left
    hd_radius = np.angle(hd_vector[:,0] + 1j*hd_vector[:,1])
    hd_degree = (hd_radius+np.pi)/(np.pi*2)*360
    return hd_degree
    

# ----------------------------------------------------------------------------
#                  Functions on 1D Env
# ----------------------------------------------------------------------------        
def find_center_circular_track(x,y, fontsize):
    # try another way, circular fitting
    # https://scipy-cookbook.readthedocs.io/items/Least_Squares_Circle.html
    def calc_R(xc, yc):
        """ calculate the distance of each 2D points from the center (xc, yc) """
        return np.sqrt((x-xc)**2 + (y-yc)**2)

    def f_2(c):
        """ calculate the algebraic distance between the data points and the mean circle centered at c=(xc, yc) """
        Ri = calc_R(*c)
        return Ri - Ri.mean()

    center_estimate = np.mean(x), np.mean(y)
    center_2,ier = optimize.leastsq(f_2, center_estimate)# could get ier or mesg, for more info of output.
    xc_2, yc_2 = center_2
    Ri_2       = calc_R(*center_2)
    R_2        = Ri_2.mean()
    residu_2   = sum((Ri_2 - R_2)**2)
    #plot for check?
    fig = plt.figure(figsize=(5,5))
    ax1 = fig.add_subplot(111)
    ax1.set_title('scatter of spatial occupancy in pixels.', fontsize=fontsize)
    ax1.scatter(np.append(x, center_2[0]), np.append(y,center_2[1]), s=3, alpha=0.1)
    return center_2, R_2, residu_2       


def boxcar_smooth_1d_circular(arr, kernel_width=20):
    arr_smo = np.convolve(np.array([1/kernel_width]*kernel_width),
                          np.concatenate((arr,arr)))[kernel_width : (arr.shape[0]+kernel_width)]
    arr_smo = np.concatenate((arr_smo[-(kernel_width):], arr_smo[:-(kernel_width)]))
    return arr_smo


def ratemap_1d_circular(spiketime, time2xy_interp, dwell_smo, nspatial_bins):
    
    spk_pol = np.angle(time2xy_interp[0](spiketime) + 1j*time2xy_interp[1](spiketime))
    spk_bin = ((spk_pol+np.pi)/(2*np.pi)*nspatial_bins).astype('uint')
    Nspike_in_bins = npg.aggregate(spk_bin, 1, size=nspatial_bins)
    Nspike_in_bins_smo = boxcar_smooth_1d_circular(Nspike_in_bins)
    ratemap = Nspike_in_bins_smo/dwell_smo
    return ratemap

def positional_information_olypher_1dcircular(spiketime, time2xy_interp, total_time, temporal_bin_length, nspatial_bins):
    t = np.linspace(0, total_time, num=(total_time/temporal_bin_length).astype('uint'), endpoint=False) + 0.5*temporal_bin_length#assign spatial values at midpoint of every time bin.
    pol = np.angle(time2xy_interp[0](t) + 1j*time2xy_interp[1](t))
    pol_temporal_bin = ((pol+np.pi)/(2*np.pi)*nspatial_bins).astype('uint')
    
    spk_time_temp = (spiketime/temporal_bin_length).astype('uint')
    # emmm this would get nearest up or down???
    
    spk_count_temporal_bin = npg.aggregate(spk_time_temp, 1, size=(total_time/temporal_bin_length).astype('uint'))
    p_k = npg.aggregate(spk_count_temporal_bin,1)/np.sum(npg.aggregate(spk_count_temporal_bin,1))
    
    pos_info = []
    for i in range(nspatial_bins):
        spk_count_temporal_bin_xi = spk_count_temporal_bin[np.where(pol_temporal_bin==i)]
        p_kxi = npg.aggregate(spk_count_temporal_bin_xi, 1)/np.sum(npg.aggregate(spk_count_temporal_bin_xi, 1))
        pos_info.append(np.sum(p_kxi * np.log2(p_kxi/p_k[:np.size(p_kxi)])))# set range for p_k is that, e.g. some time bin might have 8 spks or more but not in certain spatial bin, then arrays are not the same length. 
    return np.array(pos_info)
        
    
def shuffle_test_1d_circular(u, session, Nses, temporal_bin_length=0.02, nspatial_bins_spa=360, nspatial_bins_pos=48, p_threshold=0.01):
    # Ref, Monaco2014, head scanning, JJKnierim's paper.
    # Units must pass shuffle test and either their spa_info >1 or max_pos_info >0.4
    
    # not working well so far.
    
    units = []
    for i in u:
        if u.type == 'excitatory':
            units.append(i)
    spatial_info_pool = []
    positional_info_pool = []
    if Nses == 1:
        for i in units:
            spiketime = np.hstack((i.spiketime, i.spiketime_stay))
            spiketime = session.total_time - spiketime# invert
            spiketime.sort()
            for k in range(1000):
                spiketime += (session.total_time-8) * random.random() + 4 #offset should be at least 4s away from start/end of the session.
                spiketime[np.where(spiketime>session.total_time)] = spiketime[np.where(spiketime>session.total_time)] - session.total_time# wrap back.
                # spd_masking
                spiketime_bin_id = (spiketime/temporal_bin_length).astype('uint')
                spiketime_run = spiketime[session.spd_mask[spiketime_bin_id]]
                # spatial info
                ratemap = ratemap_1d_circular(spiketime_run, session.time2xy_interp, session.dwell_smo, nspatial_bins_spa)
                spa_info = spatial_information_skaggs(spiketime_run, ratemap, session.dwell_smo)
                spatial_info_pool.append(spa_info)
                # positional info
                pos_info = positional_information_olypher_1dcircular(spiketime_run, session.time2xy_interp, session.total_time, temporal_bin_length, nspatial_bins_pos)
                positional_info_pool.append(np.nanmax(pos_info))
                
        spatial_info_pool = np.sort(np.array(spatial_info_pool))
        positional_info_pool = np.sort(np.array(positional_info_pool))
        shuffle_bar_spa = spatial_info_pool[int(np.size(spatial_info_pool)*p_threshold) * (-1)]
        shuffle_bar_pos = positional_info_pool[int(np.size(spatial_info_pool)*p_threshold) * (-1)]
        print('Shuffle results: spatial_info {0}, postional_info {1}'.format(round(shuffle_bar_spa,4), round(shuffle_bar_pos,4)))
        for i in units:
            if i.spatial_info>shuffle_bar_spa and i.positional_info>shuffle_bar_pos:
                if i.spatial_info>1 or i.postional_info>0.4:
                    i.is_place_cell = True
    if Nses > 1:
        for i in units:
            for j in session:
                spiketime = np.hstack((i.spiketime[j.id], i.spiketime_stay[j.id]))
                spiketime = j.total_time - spiketime# invert
                spiketime.sort()
                for k in range(1000):
                    spiketime += (j.total_time-8) * random.random() + 4 #offset should be at least 4s away from start/end of the session.
                    spiketime[np.where(spiketime>j.total_time)] = spiketime[np.where(spiketime>j.total_time)] - j.total_time# wrap back.
                    # spd_masking
                    spiketime_bin_id = (spiketime/temporal_bin_length).astype('uint')
                    spiketime_run = spiketime[j.spd_mask[spiketime_bin_id]]
                    # spatial info
                    ratemap = ratemap_1d_circular(spiketime_run, j.time2xy_interp, j.dwell_smo, nspatial_bins_spa)
                    spa_info = spatial_information_skaggs(spiketime_run, ratemap, j.dwell_smo)
                    spatial_info_pool.append(spa_info)
                    # positional info
                    pos_info = positional_information_olypher_1dcircular(spiketime_run, j.time2xy_interp, j.total_time, temporal_bin_length, nspatial_bins_pos)
                    positional_info_pool.append(np.nanmax(pos_info))
                    
                    
        spatial_info_pool = np.sort(np.array(spatial_info_pool))
        positional_info_pool = np.sort(np.array(positional_info_pool))
        shuffle_bar_spa = spatial_info_pool[int(np.size(spatial_info_pool)*p_threshold) * (-1)]
        shuffle_bar_pos = positional_info_pool[int(np.size(spatial_info_pool)*p_threshold) * (-1)]
        print('Shuffle results: spatial_info {0}, postional_info {1}'.format(round(shuffle_bar_spa,4), round(shuffle_bar_pos,4)))
        for i in units:
            for j in session:
                if i.spatial_info[j.id]>shuffle_bar_spa and i.positional_info[j.id]>shuffle_bar_pos:
                    if i.spatial_info[j.id]>1 or i.postional_info[j.id]>0.4:
                        i.is_place_cell[j.id] = True


# ----------------------------------------------------------------------------
#                  Functions on 2D Env
# ----------------------------------------------------------------------------
def boxcar_smooth_2d():
    pass

def gaussian_smooth_2d():
    pass   

def shuffle_test_2d():
    # this would be simple, just go with random temporal offset and play around 1000 times. No worries like in 1d.
    pass

def Kalman_filter_2d():#interpreted from Bohua's code.
    pass

# def time2xy(ses,t):
#     return np.array(ses.time2xy_interp[0](t), (ses.time2xy_interp[1](t)))
# ----------------------------------------------------------------------------
#                  Classes session
# ----------------------------------------------------------------------------

class Session(object):    
    def __init__(self, dlch5, dlc_col_ind_dict, vsync, sync_rate, experiment_tag,
                 ses_id=0, fontsize=15):
        # docstring?           
        self.id = ses_id
        self.vsync = vsync
        self.experiment_tag = experiment_tag
        self.sync_rate = sync_rate
        self.fontsize = fontsize
        self.pixpcm = 0
        self.cut = False
        if self.experiment_tag['video record mode'] == 'Bonsai':
            self.left_pos = np.vstack((np.array(dlch5[dlch5.columns[dlc_col_ind_dict['left_pos']]]), np.array(dlch5[dlch5.columns[dlc_col_ind_dict['left_pos']+1]]))).T
            self.right_pos = np.vstack((np.array(dlch5[dlch5.columns[dlc_col_ind_dict['right_pos']]]), np.array(dlch5[dlch5.columns[dlc_col_ind_dict['right_pos']+1]]))).T 
        elif self.experiment_tag['video record mode'] == 'FrameState':
            dlcmodelstr=dlch5.columns[1][0]
            for key in dlc_col_ind_dict:# for customized need from DLC.
                pos_for_key = np.vstack((np.array(dlch5[(dlcmodelstr,key,'x')]), np.array(dlch5[(dlcmodelstr,key,'y')]))).T    
                setattr(self, key, pos_for_key)
                
            # frame_state not in input.
            for key in frame_state.columns:
                setattr(self, key, np.array(frame_state[key]).T)
            self.raw_frame_length = (getattr(self, 'Frame')).shape[0]       #mark down the total frame length of raw video, for sync cut
                

    def sync_cut_generate_frame_time(self):
        if self.experiment_tag['video record mode'] == 'Bonsai':
            if self.cut == False:
                self.left_pos = self.left_pos[self.vsync[0]:self.vsync[-1]+1, :]
                self.right_pos = self.right_pos[self.vsync[0]:self.vsync[-1]+1, :]
                #assign time values for frames. So far for a single ses, single video.
                frame2time_interp = interpolate.UnivariateSpline(self.vsync-self.vsync[0], np.linspace(0, (np.size(self.vsync)-1)/self.sync_rate, num=np.size(self.vsync)),
                                                                 k=1, s=0)
                self.frame_time = frame2time_interp(np.arange(self.left_pos.shape[0])).astype('float64')
                self.total_time = self.frame_time[-1]
                self.cut = True
            else:
                print('Has already being sync_cut, noway to do a second time.')
        elif self.experiment_tag['video record mode'] == 'FrameState':
            for key in vars(self):
                FrameData = getattr(self, key)
                if hasattr(FrameData, 'shape') and FrameData.shape[0] == self.raw_frame_length:           #if the data length quals to raw video's , it needs sync cut head tail 
                    FrameData = FrameData[self.vsync[0]:self.vsync[-1]+1]
                    setattr(self, key, FrameData)
            self.frame_length = len(self.Frame)
            frame2time_interp = interpolate.UnivariateSpline(self.vsync-self.vsync[0], np.linspace(0, (np.size(self.vsync)-1)/self.sync_rate, num=np.size(self.vsync)),k=1, s=0)
            self.frame_time = frame2time_interp(np.arange(self.framelength)).astype('float64')
            self.total_time = self.frame_time[-1]
        else:
            raise Exception('Please choose your V_recording mode.')
            

    def remove_nan_merge_pos_get_hd(self):        # this method should be split.
        nan_id = np.isnan(self.left_pos) + np.isnan(self.right_pos)
        nan_id = nan_id[:,0] + nan_id[:,1]
        nan_id = np.where(nan_id == 2, 1, 0).astype('bool')
        self.frame_time = self.frame_time[~nan_id]
        self.left_pos = self.left_pos[~nan_id]
        self.right_pos = self.right_pos[~nan_id]      
        if self.experiment_tag['theme'] == 'spatial':
            hd_vector = self.right_pos - self.left_pos
            hd_radius = np.angle(hd_vector[:,0] + 1j*hd_vector[:,1])
            self.hd_degree = (hd_radius+np.pi)/(np.pi*2)*360
            
        
        self.pos_pix = (self.left_pos + self.right_pos)/2   #this is another function. should be decoupled.
        if self.experiment_tag['maze shape'] == 'circular':
            self.pos = ((self.left_pos + self.right_pos)/2 - self.center[0])/self.pixpcm
        else:
            print('you need to code your way do define pixels per cm, to go furthur.')
    
    def generate_time2xy_interpolate(self, mode='linear'):
        if mode == 'cspline':
            # using scipy.interpolate.UnivariateSpline seperately with x&y might cause some infidelity. Mind this.
            # k = 3, how to set a proper smooth factor s???
            # what about it after Kalman filter?
            # how to check this???
            time2x_interp = interpolate.UnivariateSpline(self.frame_time, self.pos[:,0])
            time2y_interp = interpolate.UnivariateSpline(self.frame_time, self.pos[:,1])
            time2x_left = interpolate.UnivariateSpline(self.frame_time, self.left_pos[:,0])
            time2y_left = interpolate.UnivariateSpline(self.frame_time, self.left_pos[:,1])
            time2x_right = interpolate.UnivariateSpline(self.frame_time, self.right_pos[:,0])
            time2y_right = interpolate.UnivariateSpline(self.frame_time, self.right_pos[:,1])
        elif mode == 'linear':
            time2x_interp = interpolate.UnivariateSpline(self.frame_time, self.pos[:,0], k=1)
            time2y_interp = interpolate.UnivariateSpline(self.frame_time, self.pos[:,1], k=1)
            time2x_left = interpolate.UnivariateSpline(self.frame_time, self.left_pos[:,0], k=1)
            time2y_left = interpolate.UnivariateSpline(self.frame_time, self.left_pos[:,1], k=1)
            time2x_right = interpolate.UnivariateSpline(self.frame_time, self.right_pos[:,0], k=1)
            time2y_right = interpolate.UnivariateSpline(self.frame_time, self.right_pos[:,1], k=1)
        self.time2xy_interp = (time2x_interp, time2y_interp, time2x_left, time2y_left, time2x_right, time2y_right)


    def generate_spd_mask_20ms_bin(self, threshold=2, temporal_bin_length=0.02):
        t = np.linspace(0, self.total_time, num=(self.total_time/temporal_bin_length +1).astype('uint'))
        x = self.time2xy_interp[0](t)
        y = self.time2xy_interp[1](t)
        dist = np.sqrt((x[1:]-x[:-1])**2 + (y[1:]-y[:-1])**2)
        self.inst_spd = dist/temporal_bin_length
        self.spd_mask = np.where(self.inst_spd > 2, 1, 0)
        self.spd_mask = np.append(self.spd_mask, 0).astype('bool')# for convinience.
    
# -----------------------------------------------------------------------------
#                 Derived Classes from Session
# -----------------------------------------------------------------------------
class DetourSession(Session):
    def __init__(self, dlch5, dlc_col_ind_dict, frame_state, vsync, sync_rate, expriment_tag, ses_id=0, fontsize=15):
        Session.__init__(self, dlch5, dlc_col_ind_dict, vsync, sync_rate, experiment_tag, ses_id, fontsize)
                
def generate_interpolater(self):
    time2frame = interpolate.interp1d(self.frametime, np.linspace(0, (np.size(self.frametime)-1),num=np.size(self.frametime)), kind='nearest')
    self.get = {'time2frame':time2frame }
    
    def time2index(spiketime):
        frame_id = self.get['time2frame'](spiketime)
        return int(frame_id)
    def generate_index_func(obj, key):
        def FUNC(spiketime):
            return getattr(obj, key)[time2index(spiketime)]
        return FUNC
    def generate_mergeXY_func(obj, key):
        def FUNC(spiketime):
            return [obj.get[key+'X'](spiketime),obj.get[key+'Y'](spiketime)]
        return FUNC
                
    for key in vars(self):
        FrameData = getattr(self, key)
        if hasattr(FrameData, 'shape') and FrameData.shape[0] == self.frame_length:
            if type(FrameData[0]) == np.bool_ :                             #如果是bool值，那么在进行插值的时候应该取最邻近的值，而且bool值可以被数字比大小，所以单独写一个分支
                 self.get[key] = generate_index_func(self, key) 
            elif type(FrameData[0]) == str :                                #如果是字符串，那么在进行插值的时候应该取最邻近的值
                self.get[key] = generate_index_func(self, key) 
            elif type(FrameData[0]) == np.ndarray :                         #如果是一个数组，那意味着选到了某个位置（x，y），所以分别对x，y做插值，输出一个（x，y）
                self.get[key+'X'] = interpolate.UnivariateSpline(self.frametime, FrameData[:,0])
                self.get[key+'Y'] = interpolate.UnivariateSpline(self.frametime, FrameData[:,1])
                self.get[key] = generate_mergeXY_func(self, key) 
            elif FrameData[0] >= 0:                                         #如果是一个数字
                self.get[key] = interpolate.UnivariateSpline(self.frametime, FrameData)
            else:
                raise Exception('Error in generating interpolater, value type not defined')
            
    
def slowget(self, key, spiketime):
    ValueSet = getattr(self, key)
        
    if type(ValueSet[0]) == np.bool_ :        #如果是bool值，那么在进行插值的时候应该取最邻近的值，而且bool值可以被数字比大小，所以单独写一个分支
        Interpolater = interpolate.interp1d(self.frametime, ValueSet, kind='previous')
        ValueAtTime = Interpolater(spiketime)
        return ValueAtTime
        
    elif type(ValueSet[0]) == str :           #如果是字符串，那么在进行插值的时候应该取最邻近的值
        Interpolater = interpolate.UnivariateSpline(self.frametime, ValueSet)
        ValueAtTime = Interpolater(spiketime)
        return ValueAtTime
        
    elif type(ValueSet[0]) == np.ndarray :    #如果是一个数组，那意味着选到了某个位置（x，y），所以分别对x，y做插值，输出一个（x，y）
        InterpolaterX = interpolate.UnivariateSpline(self.frametime, ValueSet[:,0])
        InterpolaterY = interpolate.UnivariateSpline(self.frametime, ValueSet[:,1])
        ValueAtTime = [InterpolaterX(spiketime),InterpolaterY(spiketime)]
        return ValueAtTime
        
    elif ValueSet[0] >=0 :              #如果是一个数字
        Interpolater = interpolate.UnivariateSpline(self.frametime, ValueSet)
        ValueAtTime = Interpolater(spiketime)
        return ValueAtTime        
    else:
        raise Exception('You acquired wrong variable')








class DRsession(Session):
    def __init__(self, dlch5, dlc_col_ind_dict, vsync, sync_rate, experiment_tag,
                 ses_id=0, fontsize=15):
        Session.__init__(self, dlch5, dlc_col_ind_dict, vsync, sync_rate, experiment_tag, ses_id, fontsize)
        if self.experiment_tag['maze shape'] == 'circular':
            self.center = find_center_circular_track(np.vstack((self.left_pos, self.right_pos))[:,0], np.vstack((self.left_pos, self.right_pos))[:,1], fontsize=self.fontsize)
            self.pixpcm = 2*self.center[1]/65
    
    def generate_dwell_map_circular(self, nspatial_bins=360, smooth='boxcar', temporal_bin_length=0.02):
        if self.experiment_tag['maze shape'] != 'circular':
            print('wrong method was chosen.')
        else:
            #just a repeat after spd_mask.
            self.pol = np.angle(self.pos[:,0] + 1j*self.pos[:,1])
            self.pol_bin = ((self.pol+np.pi)/np.pi*nspatial_bins/2).astype('uint')
            
            # temporal resample for spd_mask
            t = np.linspace(0, self.total_time, num=(self.total_time/temporal_bin_length +1).astype('uint'))
            self.pos_resample = np.vstack((self.time2xy_interp[0](t), self.time2xy_interp[1](t))).T
            self.pol_resample = np.angle(self.pos_resample[:,0] + 1j*self.pos_resample[:,1])
            self.pol_bin_resample = ((self.pol_resample+np.pi)/np.pi*nspatial_bins/2).astype('uint')
            
            #apply spd_mask.
            dwell = npg.aggregate(self.pol_bin_resample[self.spd_mask], temporal_bin_length, size=nspatial_bins)
            # emmm....so where is 0 degree???  It is Right.
            pol_bin_1half = self.pol_bin_resample[:int(np.size(self.pol_bin_resample)/2)]
            spd_mask_1half = self.spd_mask[:int(np.size(self.pol_bin_resample)/2)]
            pol_bin_2half = self.pol_bin_resample[int(np.size(self.pol_bin_resample)/2):]
            spd_mask_2half = self.spd_mask[int(np.size(self.pol_bin_resample)/2):]
            dwell_1half = npg.aggregate(pol_bin_1half[spd_mask_1half], temporal_bin_length, size=nspatial_bins)
            dwell_2half = npg.aggregate(pol_bin_2half[spd_mask_2half], temporal_bin_length, size=nspatial_bins)

            if smooth == 'boxcar':
                self.dwell_smo = boxcar_smooth_1d_circular(dwell)
                self.dwell_1half_smo = boxcar_smooth_1d_circular(dwell_1half)
                self.dwell_2half_smo = boxcar_smooth_1d_circular(dwell_2half)
            else:
                print('for other type of kernels... to be continue...')
            
            fig = plt.figure(figsize=(5,15))
            ax1 = fig.add_subplot(311)
            ax1.set_title('spd check', fontsize=self.fontsize*1.3)
            ax1.hist(self.inst_spd, range = (0,70), bins = 100)
            spd_bin_max = np.max(np.bincount(self.inst_spd.astype('uint'), minlength=100))
            ax1.plot(([np.median(self.inst_spd)]*2), [0, spd_bin_max*0.7], color='k')
            ax1.set_xlabel('animal spd cm/s', fontsize=self.fontsize)
            ax1.set_ylabel('N 20ms teporal bins', fontsize=self.fontsize)
            ax2 = fig.add_subplot(312)
            ax2.set_title('animal spatial occupancy', fontsize=self.fontsize)
            ax2.plot(np.linspace(1, nspatial_bins, num=nspatial_bins, dtype='int'), self.dwell_smo, color='k')
            ax2.plot(np.linspace(1, nspatial_bins, num=nspatial_bins, dtype='int'), self.dwell_1half_smo, color='r')
            ax2.plot(np.linspace(1, nspatial_bins, num=nspatial_bins, dtype='int'), self.dwell_2half_smo, color='b')
            ax2.set_ylim(0, np.max(self.dwell_smo)*1.1)
            ax2.set_xlabel('spatial degree-bin', fontsize=self.fontsize)
            ax2.set_ylabel('occupancy in sec', fontsize=self.fontsize)
            ax3 = fig.add_subplot(313)
            ax3.scatter(self.pol, np.linspace(0, self.total_time, num=np.size(self.pol)), c='k', s=0.1)
            ax3.set_title('animal trajectory', fontsize=self.fontsize*1.3)
            ax3.set_xlabel('position in radius degree.', fontsize=self.fontsize)
            ax3.set_ylabel('time in sec', fontsize=self.fontsize)


            

        

 # ----------------------------------------------------------------------------
 #                  Classes unit
 # ----------------------------------------------------------------------------
 
class Unit(object):
    def __init__(self, cluid, spike_pack, quality, Nses, experiment_tag, fontsize):
        self.cluid = cluid
        self.quality = quality
        self.type = 'unknown'#IN or PC  
        self.meanwaveform = []
        self.Nses = Nses
        self.fontsize = fontsize
        self.experiment_tag = experiment_tag


        if Nses == 1 and self.experiment_tag['theme'] == 'spatial':
            # unpacking spike_pack.
            spike_pick_cluid = np.where(spike_pack[0] == self.cluid)[0]
            self.timestamps = spike_pack[1][spike_pick_cluid]
            self.spiketime = spike_pack[2][spike_pick_cluid]
            spike_stay_pick_cluid = np.where(spike_pack[3] == self.cluid)[0]
            self.timestamps_stay = spike_pack[4][spike_stay_pick_cluid]
            self.spiketime_stay = spike_pack[5][spike_stay_pick_cluid]
            self.Nspikes_total = np.size(self.timestamps) + np.size(self.timestamps_stay)
            # initialize spa. params.
            self.ratemap = []
            self.peakrate = []
            self.spatial_info = []
            self.positional_info = []
            self.stability = []
            self.global_mean_rate = []
            self.__running_mean_rate = []
            self.is_place_cell = False
        elif Nses > 1 and self.experiment_tag['theme'] == 'spatial':
            self.timestamps = [0 for i in range(Nses)]
            self.spiketime = [0 for i in range(Nses)]
            self.timestamps_stay = [0 for i in range(Nses)]
            self.spiketime_stay = [0 for i in range(Nses)]
            self.Nspikes_total = [0 for i in range(Nses)] 
            self.ratemap = [0 for i in range(Nses)]
            self.peakrate = [0 for i in range(Nses)]
            self.spatial_info = [0 for i in range(Nses)]
            self.positional_info = [0 for i in range(Nses)]
            self.stability = [0 for i in range(Nses)]
            self.global_mean_rate = [0 for i in range(Nses)]
            self.__running_mean_rate = [0 for i in range(Nses)]
            self.is_place_cell = [False for i in range(Nses)]
            # unpacking
            for i in range(Nses):
                spike_pick_cluid = np.where(spike_pack[i][0] == self.cluid)[0]
                spike_stay_pick_cluid = np.where(spike_pack[i][3] == self.cluid)[0]
                self.timestamps[i] = spike_pack[i][1][spike_pick_cluid]
                self.spiketime[i] = spike_pack[i][2][spike_pick_cluid]
                self.timestamps_stay[i] = spike_pack[i][4][spike_stay_pick_cluid]
                self.spiketime_stay[i] = spike_pack[i][5][spike_stay_pick_cluid]
                self.Nspikes_total[i] = np.size(self.timestamps[i]) + np.size(self.timestamps_stay[i])
            
        elif Nses == 1 and self.experiment_tag['theme'] != 'spatial':
            spike_pick_cluid = np.where(spike_pack[0] == self.cluid)[0]
            self.timestamps = spike_pack[1][spike_pick_cluid]
            self.spiketime = spike_pack[2][spike_pick_cluid]
        
        elif Nses > 1 and self.experiment_tag['theme'] != 'spatial':
            self.timestamps = [0 for i in range(Nses)]
            self.spiketime = [0 for i in range(Nses)]
            for i in Nses:
                spike_pick_cluid = np.where(spike_pack[i][0] == self.cluid)[0]
                spike_stay_pick_cluid = np.where(spike_pack[i][4] == self.cluid)[0]
                self.timestamps[i] = spike_pack[i][1][spike_pick_cluid]
                self.spiketime[i] = spike_pack[i][2][spike_pick_cluid]
        else:
            print('Wrong input for unit.')


                                

            
    def simple_putative_IN_PC_by_firingrate(self, ses):
        # this is a simple way to put IN and PC not by waveform but only global mean firing rate.
        # see Nuenuebel 2013, DR with L/MEC, threshold of mean firing rate is 10Hz.
        if self.experiment_tag['theme'] == 'spatial':
            if self.Nses == 1:
                if self.global_mean_rate > 10:
                    self.type = 'inhibory'
                else:
                    self.type = 'excitatory'
            else:
                ses_inds = [i.id for i in ses]
                if (np.array(self.global_mean_rate)[ses_inds].all() > 10).all() == True:
                    self.type = 'inhibitory'
                elif (np.array(self.global_mean_rate)[ses_inds] < 10).all() == True:
                    self.type = 'excitatory'
                else:
                    self.type = 'unsure' 
        else:
            raise Exception('you might used wrong method.')
            
    def report_spatial(self):
        if self.experiment_tag['theme'] == 'spatial':
            print('cluster id:', self.cluid, '\n Nspike:', self.Nspikes_total, '\n peakrate:', self.peakrate, '\n mean rate while running:', self.__running_mean_rate, '\n spa. info:', self.spatial_info, '\n stability:', self.stability)
        else:
            raise Exception('you might used wrong method.')
    
    

   
         
    def opto_inhibitory_tagging(self, ses, signal_on_time, mode, p_threshold=0.01, laser_on_sec=20, laser_off_sec=20, shuffle_range_sec=20):
        # it takes laser on as start of a cycle.
        if self.Nses == 1:
            signal_on_temp = signal_on_time
        else:
            signal_on_temp = signal_on_time[ses.id]
        if self.experiment_tag['theme'] == 'spatial':
            spike_time = np.concatenate((self.spiketime[ses.id], self.spiketime_stay[ses.id]))
        else:
            spike_time = self.spiketime
        if mode == 'ranksum':# in ranksum test mode, shuffle range is not used.
            on_spk_count = []
            off_spk_count = []
            for i in range(np.size(signal_on_temp)):
                spike_time_temp = spike_time[np.where(spike_time < (signal_on_temp[i] + laser_on_sec))]
                spike_time_temp = spike_time_temp[np.where(spike_time_temp > signal_on_temp[i])]
                on_spk_count.append(np.size(spike_time_temp))
                spike_time_temp2 = spike_time[np.where(spike_time < (signal_on_temp[i] + (laser_on_sec+laser_off_sec)))]
                spike_time_temp2 = spike_time_temp2[np.where(spike_time_temp2 > (signal_on_temp[i] + laser_on_sec))]
                off_spk_count.append(np.size(spike_time_temp2))
            statistic, pvalue = stats.ranksums(on_spk_count, off_spk_count, alternative='less')
            if pvalue < p_threshold:
                print('clu{} is positive, p-value'.format(self.cluid), pvalue)
                self.opto_tag = 'positive'
            # emmm...how to deal with margitial?
            else:
                print('clu{} is negative, p-value'.format(self.cluid), pvalue)
                self.opto_tag = 'negative'
        elif mode == 'shuffle':
            raise Exception('shuffle test is not finished yet')
            # 1000times, 0.01
            pass            
        else:
            raise Exception('Wrong mode or the mode has not been coded.')

    def plot_PSTH(self, ses):
        pass


 # ----------------------------------------------------------------------------
 #            Derived Classes of Unit
 # ----------------------------------------------------------------------------

class Unit1DCircular(Unit):
    def __init__(self, cluid, spike_pack, quality, Nses, experiment_tag, fontsize):
        super().__init__(cluid, spike_pack, quality, Nses, experiment_tag, fontsize)
        

    def get_ratemap_1d_circular(self, ses, nspatial_bins=360):
        if self.experiment_tag['maze shape'] == 'circular' and self.experiment_tag['theme'] == 'spatial':
            if self.Nses == 1:
                self.ratemap = ratemap_1d_circular(self.spiketime, ses.time2xy_interp, ses.dwell_smo, nspatial_bins)
                self.peakrate = round(np.max(self.ratemap),2)
            else:
                self.ratemap[ses.id] = ratemap_1d_circular(self.spiketime[ses.id], ses.time2xy_interp, ses.dwell_smo, nspatial_bins)
                self.peakrate[ses.id] = round(np.max(self.ratemap[ses.id]),2)       
        else:
            print('you might used wrong method.')


    def get_spatial_info_Skaggs(self, ses):
        if self.experiment_tag['theme'] == 'spatial':
            if self.Nses == 1:
                self.spatial_info, self.global_mean_rate = spatial_information_skaggs(self.timestamps, self.ratemap, ses.dwell_smo)
            else:
                self.spatial_info[ses.id], self.global_mean_rate[ses.id] = spatial_information_skaggs(self.timestamps[ses.id], self.ratemap[ses.id], ses.dwell_smo)
        else:
            print('you might used wrong method.')
 
            
    def get_positional_info_Olyper(self, ses, temporal_bin_length=0.1, nspatial_bins=48):
        if self.experiment_tag['theme'] == 'spatial':
            if self.Nses == 1:
                self.positional_info = positional_information_olypher_1dcircular(self.spiketime, ses.time2xy_interp, ses.total_time, temporal_bin_length, nspatial_bins)
            else:
                self.positional_info[ses.id] = positional_information_olypher_1dcircular(self.spiketime[ses.id], ses.time2xy_interp, ses.total_time, temporal_bin_length, nspatial_bins)
        

    def get_stability_1d_circular(self, ses, nspatial_bins=360):
        if self.experiment_tag['maze shape'] == 'circular' and self.experiment_tag['theme'] == 'spatial':
            if self.Nses == 1:
                spike_time_1half = self.spiketime[np.where(self.spiketime < ses.frame_time[-1]/2)]
                spike_time_2half = self.spiketime[np.where(self.spiketime > ses.frame_time[-1]/2)]
                ratemap_1half = ratemap_1d_circular(spike_time_1half, ses.time2xy_interp, ses.dwell_1half_smo, nspatial_bins)
                ratemap_2half = ratemap_1d_circular(spike_time_1half, ses.time2xy_interp, ses.dwell_2half_smo, nspatial_bins)
                self.stability = round(np.corrcoef(np.vstack((ratemap_1half,ratemap_2half)))[1,0],2)
            else:
                spike_time_1half = self.spiketime[ses.id][np.where(self.spiketime[ses.id] < ses.frame_time[-1]/2)]
                spike_time_2half = self.spiketime[ses.id][np.where(self.spiketime[ses.id] > ses.frame_time[-1]/2)]
                ratemap_1half = ratemap_1d_circular(spike_time_1half, ses.time2xy_interp, ses.dwell_1half_smo, nspatial_bins)
                ratemap_2half = ratemap_1d_circular(spike_time_1half, ses.time2xy_interp, ses.dwell_2half_smo, nspatial_bins)
                self.stability[ses.id] = round(np.corrcoef(np.vstack((ratemap_1half,ratemap_2half)))[1,0],2)
        else:
            raise Exception('you might used wrong method.')
 
    
    def plot_spike_position(self, ses, color_list=['k','b','k','cyan','orange'], opto_tag=True):
        if self.experiment_tag['maze shape'] == 'circular' and self.experiment_tag['theme'] == 'spatial':
            if self.Nses == 1:
                # later
                pass
            else:
 
            #EMMM...standard way using Figure.axes
                fig = plt.figure(figsize=(30,6), dpi=200)
                for i in range(self.Nses):
                    fig.add_subplot(1, self.Nses, i+1)
                    t = np.linspace(0, ses[i].total_time, num=ses[i].total_time.astype('uint')*20, dtype='float32')
                    x = ses[i].time2xy_interp[0](t)
                    y = ses[i].time2xy_interp[1](t)
                    angle = ((np.angle(x + 1j*y)/np.pi)+1)*180# radius2degre
                    fig.axes[i].scatter(angle, t, s=2, marker='_', color='grey')
                    x2 = ses[i].time2xy_interp[0](self.spiketime[i])
                    y2 = ses[i].time2xy_interp[1](self.spiketime[i])
                    angle2 = ((np.angle(x2 + 1j*y2)/np.pi)+1)*180
                    fig.axes[i].scatter(angle2, self.spiketime[i], marker='|', color=color_list[i], s=40)
                    fig.axes[i].set_xticks([0,90,180,270,360])
                fig.axes[0].set_ylabel('time in second', fontsize=self.fontsize)
                fig.axes[2].set_xlabel('position in degree', fontsize=self.fontsize)
                fig.axes[2].set_title('clu{0}, {1}, {2}'.format(str(self.cluid), self.quality, self.opto_tag),fontsize=self.fontsize*1.2)
            # Plus, add a opto tagging check with fillbetween
                       
        else:
            raise Exception('you might used wrong method.')
 
    
    # def plot_ratemap_1d_circular_polar(self, ses, nspatial_bins=360,
    #                                    color_list=['k','b','grey','cyan','orange'], 
    #                                    legend_list=['standard1', '135 degree conflict', 'standard2', '45 degree conflict', 'inhibitary tagging']):
    #     if self.experiment_tag['maze shape'] == 'circular' and self.experiment_tag['theme'] == 'spatial':
    #         fig = plt.figure(figsize=(12,7))
    #         ax1 = fig.add_subplot(121, polar=True)
    #         ax1.set_theta_direction('clockwise')
    #         ax1.set_theta_offset(np.pi/2)
    #         ax2 = fig.add_subplot(122)
    #         if self.Nses == 1:
    #             theta = np.linspace(0, 2*np.pi, num=nspatial_bins)
    #             ax1.plot(theta, self.ratemap, c=color_list[ses.id])
    #             ax2.plot(self.ratemap, c=color_list[ses.id])
    #             ax1.legend(legend_list[0], fontsize=self.fontsize, loc='lower right')
    #         else:
    #             theta = np.linspace(0, 2*np.pi, num=nspatial_bins)
    #             for i in ses:
    #                 ax1.plot(theta, self.ratemap[i.id], c=color_list[i.id])
    #                 ax2.plot(self.ratemap[i.id], c=color_list[i.id])
    #             ax1.legend(legend_list, fontsize=self.fontsize, loc='lower right')
    #         ax1.set_title('ratemap in 5 sessions, clu'+str(self.cluid)+', '+str(self.quality), fontsize=self.fontsize*1.3)
    #         ax2.set_title('spa. info ='+str(self.spatial_info), fontsize=self.fontsize*1.3)
    #         ax1.set_xlabel('spatial bin', fontsize=self.fontsize)
    #         ax1.set_ylabel('firing rate', fontsize=self.fontsize)
    #         ax2.set_xlabel('spatial bins', fontsize=self.fontsize)
    #         ax2.set_ylabel('firing rate', fontsize=self.fontsize)
    #     else:
    #         raise Exception('you might used wrong method.')
            
    def plot_ratemap_DRexample(self, ses1id, ses2id, fpath,
                               color=['grey','black']):
        # only for show. this will mask those away from main field.
        offset = np.where(self.ratemap[ses1id] == np.nanmax(self.ratemap[ses1id]))[0]
        offset = -(offset/180) *np.pi
        fig = plt.figure(figsize=(5,5))
        ax = fig.add_subplot(111, polar=True)
        ax.set_theta_direction('clockwise')
        ax.set_theta_offset(np.pi/2)
        # just for show.
        ratemap1 = self.ratemap[ses1id]/np.max(self.ratemap[ses1id])
        ratemap2 = self.ratemap[ses2id]/np.max(self.ratemap[ses2id])
        peak1 = np.where(self.ratemap[ses1id] == np.max(self.ratemap[ses1id]))[0]
        peak2 = np.where(self.ratemap[ses2id] == np.max(self.ratemap[ses2id]))[0]
        mask = np.zeros(360)
        if peak1 > 25 and peak1 < 335:
            mask1 = mask.copy()
            mask1[int(peak1-22):int(peak1+23)] = 1
            ratemap1 = ratemap1 * mask1
        else:
            ratemap1 = np.concatenate((ratemap1[180:], ratemap1[:180]), axis=0)
            mask1 = mask.copy()
            mask1[int(peak1+158):int(peak1+203)] = 1
            ratemap1 = ratemap1 * mask1
            ratemap1 = np.concatenate((ratemap1[180:], ratemap1[:180]), axis=0)
        if peak2 > 25 and peak2 < 335:
            mask2 = mask.copy()
            mask2[int(peak2-22):int(peak2+23)] = 1
            ratemap2 = ratemap2 * mask2
        else:
            ratemap2 = np.concatenate((ratemap2[180:], ratemap2[:180]), axis=0)
            mask2 = mask.copy()
            mask2[int(peak2+158):int(peak2+203)] = 1
            ratemap2 = ratemap2 * mask2
            ratemap2 = np.concatenate((ratemap2[180:], ratemap2[:180]), axis=0)
            
        theta = np.linspace(0, 2*np.pi, num=np.size(self.ratemap[0]))
        ax.plot(theta+offset, ratemap1, color=color[0])
        ax.plot(theta+offset, ratemap2, color=color[1])
        fig.savefig(fpath, format='svg')

        

    def simple_is_place_cell_DR(self):
        # only used before shuffle test works.
        self.is_place_cell = [False for i in range(self.Nses)]
        for i in range(self.Nses):
            if (self.spatial_info[i] > 1 or np.nanmax(self.positional_info[i]) > 0.8) and np.nanmax(self.peakrate[i]) > 4:
                self.is_place_cell[i] = True

    # def rotational_correlation_DR(self, ses1, ses2, nspatial_bins=360, bin_increment=3):
    #     if 'DR' not in self.experiment_tag:
    #         print('Wrong method was used.')
    #     else:
    #         rotational_corrcoef = [np.corrcoef(self.ratemap[ses1.id], self.ratemap[ses2.id])[0,1]]
            
    #         #这里可以说是方向写错了。进动方向反了，出图会比较绕。
            
    #         for i in range(bin_increment, nspatial_bins, bin_increment):
    #             ratemap_rotate = np.concatenate((self.ratemap[ses2.id][i:],self.ratemap[ses2.id][:i]))
    #             rotational_corrcoef.append(np.corrcoef(self.ratemap[ses1.id], ratemap_rotate)[0,1])
            
    #         rotational_corrcoef = np.array(rotational_corrcoef)
    #         fig = plt.figure(figsize=(5,5))
    #         ax1 = fig.add_subplot(111)
    #         x = np.linspace(0, 360, num=int(nspatial_bins/bin_increment), endpoint=False)
    #         ax1.plot(x, rotational_corrcoef, c='r')
    #         ax1.plot(x, [0.75]*np.size(x), c='green')
    #         ax1.set_title('rota. corr. of clu'+str(self.cluid)+' ')
    #         try:
    #             self.rotational_correlation_peak.append(np.where(rotational_corrcoef == np.max(rotational_corrcoef))[0][0]*bin_increment)
    #         except:
    #             self.rotational_correlation_peak = [np.where(rotational_corrcoef == np.max(rotational_corrcoef))[0][0]*bin_increment]
                
    def plot_ratemap_and_rotational_corr(self, ses, nspatial_bins=360, bin_increment = 3,
                                         conflict_ses=[1,3],
                                         color_list=['k','b','grey','cyan','orange'],
                                         legend_list=['standard1', '90 degree conflict', 'standard2', '180 degree conflict', 'inhibitory tagging'],
                                         signal_on_time=False, signal_on_ses=4, pre_sec=20, post_sec=20, stim_color='yellow'):
        if self.experiment_tag['signal'] == 'inhibitory tagging':
            subplots = 4
        else:
            subplots = 3
        fig, axes = plt.subplots(1, subplots, figsize=(subplots*6,7), layout='constrained')
        axes[0].set_axis_off()#HAHAHAHAHAHA EVIL CODING
        axes[0] = fig.add_subplot(1, subplots, 1, projection='polar')
        
        fig.suptitle('ratemap in {0} sessions, clu{1}, {2}, {3}'.format(self.Nses, self.cluid, self.quality, self.type), fontsize=self.fontsize*1.2)
        axes[0].set_title('spa. info ='+str([round(i,2) for i in self.spatial_info]), fontsize = self.fontsize*1.2)
        axes[0].set_theta_direction('clockwise')
        axes[0].set_theta_offset(np.pi/2)
        theta = np.linspace(0, 2*np.pi, num=nspatial_bins)
        for i in ses:
            axes[0].plot(theta, self.ratemap[i.id], c=color_list[ses.index(i)])
            axes[1].plot(self.ratemap[i.id], c=color_list[ses.index(i)])
        axes[0].legend(legend_list, fontsize=self.fontsize, loc='lower left')
        axes[1].set_title('pos. info ='+str([round(np.nanmax(i),2) for i in self.positional_info]), fontsize = self.fontsize*1.2)
        axes[0].set_xlabel('spatial bins in degree', fontsize=self.fontsize)
        axes[0].set_ylabel('firing rate', fontsize=self.fontsize)
        axes[1].set_xlabel('spatial bins', fontsize=self.fontsize)
        axes[1].set_ylabel('firing rate', fontsize=self.fontsize)
        
        #20231120 check direction of rot. simi.
        rotational_corrcoef1 = [np.corrcoef(self.ratemap[conflict_ses[0]], self.ratemap[conflict_ses[0]-1])[0,1]]
        rotational_corrcoef2 = [np.corrcoef(self.ratemap[conflict_ses[1]], self.ratemap[conflict_ses[1]-1])[0,1]]
        for i in range(bin_increment, nspatial_bins, bin_increment):
            ratemap_rotate1 = np.concatenate((self.ratemap[conflict_ses[0]][i:],self.ratemap[conflict_ses[0]][:i]))
            rotational_corrcoef1.append(np.corrcoef(self.ratemap[conflict_ses[0]-1], ratemap_rotate1)[0,1])
            ratemap_rotate2 = np.concatenate((self.ratemap[conflict_ses[1]][i:],self.ratemap[conflict_ses[1]][:i]))
            rotational_corrcoef2.append(np.corrcoef(self.ratemap[conflict_ses[1]-1], ratemap_rotate2)[0,1])
        # in this way, the rot. simi. goes in a counterclockwise way. So flipud, then it's c-wise
        rotational_corrcoef1 = np.array(rotational_corrcoef1)
        rotational_corrcoef2 = np.array(rotational_corrcoef2)

        x = np.linspace(0, 360, num=int(nspatial_bins/bin_increment), endpoint=False)
        axes[2].plot(x, rotational_corrcoef1, c='b')
        axes[2].plot(x, rotational_corrcoef2, c='cyan')
        axes[2].plot([180,180], [-0.2,1], linestyle='dashed', c='grey')
        axes[2].plot(x, [0.6]*np.size(x), c='red')
        # as in Knierim 2002 the criteria include peak corr greater than 0.75.
        # might be too high, try 2013 EC, 0.6
        self.rotational_correlation_peak = []
        if np.max(rotational_corrcoef1) > 0.6 and (self.is_place_cell[conflict_ses[0]] & self.is_place_cell[conflict_ses[0]-1]) == True:
            self.rotational_correlation_peak.append(np.where(rotational_corrcoef1 == np.max(rotational_corrcoef1))[0][0]*bin_increment)
        else:
            self.rotational_correlation_peak.append(False)
        if np.max(rotational_corrcoef2) > 0.6 and (self.is_place_cell[conflict_ses[1]] & self.is_place_cell[conflict_ses[1]-1]) == True:
            self.rotational_correlation_peak.append(np.where(rotational_corrcoef2 == np.max(rotational_corrcoef2))[0][0]*bin_increment)
        else:
            self.rotational_correlation_peak.append(False)
        axes[2].set_title('rota. corr. of clu'+str(self.cluid)+' '+str(self.rotational_correlation_peak), fontsize=self.fontsize*1.2)
        
        if self.experiment_tag['signal'] == 'inhibitory tagging':
            axes[3].set_title('PSTH around laser-on, '+self.opto_tag, fontsize=self.fontsize*1.3)
            axes[3].set_xlabel('Time in sec', fontsize=self.fontsize)
            axes[3].set_xlim(left=-(pre_sec), right=post_sec)
            axes[3].set_ylabel('Trials', fontsize=self.fontsize)
            signal_on_temp = signal_on_time[signal_on_ses-1]
            axes[3].set_ylim(bottom=1, top=np.size(signal_on_temp)+1)
            if self.experiment_tag['theme'] == 'spatial':
                spike_time = np.concatenate((self.spiketime[signal_on_ses-1], self.spiketime_stay[signal_on_ses-1]))
            else:
                spike_time = self.spike_time[signal_on_ses-1]
            for i in range(np.size(signal_on_temp)):
                spike_time_temp = spike_time[np.where(spike_time < (signal_on_temp[i] + post_sec))]
                spike_time_temp = spike_time_temp[np.where(spike_time_temp > (signal_on_temp[i] - pre_sec))].astype('float64')
                spike_time_temp = spike_time_temp - signal_on_temp[i]
                axes[3].scatter(spike_time_temp, np.array([i+1]*np.size(spike_time_temp)).astype('uint16'), c='k', marker='|', s=40)
            axes[3].fill_between([0, post_sec], 0, np.size(signal_on_temp)+1, facecolor=stim_color, alpha=0.5)
            fig.layout_engine = 'constrained'
        
        
        
    def DR_standard_check(self, ses, nspatial_bins=360, bin_increment = 3,
                                         color_list=['k','white','grey','white','orange']):
        fig = plt.figure(figsize=(18,7))
        ax1 = fig.add_subplot(131, polar=True)
        ax1.set_theta_direction('clockwise')
        ax1.set_theta_offset(np.pi/2)
        ax2 = fig.add_subplot(132)
        theta = np.linspace(0, 2*np.pi, num=nspatial_bins)
        for i in ses:
            ax1.plot(theta, self.ratemap[i.id], c=color_list[i.id])
            ax2.plot(self.ratemap[i.id], c=color_list[i.id])
        ax1.set_title('clu'+str(self.cluid)+', '+str(self.quality)+', '+self.opto_tag, fontsize=self.fontsize*1.2)
        ax2.set_title('spa. info ='+str([round(i,2) for i in self.spatial_info])+'\n pos. info ='+
                      str([round(np.nanmax(i),2) for i in self.positional_info]), fontsize = self.fontsize*1.2)
        ax1.set_xlabel('spatial bins in degree', fontsize=self.fontsize)
        ax1.set_ylabel('firing rate', fontsize=self.fontsize)
        ax2.set_xlabel('spatial bins', fontsize=self.fontsize)
        ax2.set_ylabel('firing rate', fontsize=self.fontsize)
        
        
        rotational_corrcoef1 = [np.corrcoef(self.ratemap[ses[0].id], self.ratemap[ses[2].id])[0,1]]
        rotational_corrcoef2 = [np.corrcoef(self.ratemap[ses[2].id], self.ratemap[ses[4].id])[0,1]]
        for i in range(bin_increment, nspatial_bins, bin_increment):
            ratemap_rotate1 = np.concatenate((self.ratemap[ses[2].id][i:],self.ratemap[ses[2].id][:i]))
            rotational_corrcoef1.append(np.corrcoef(self.ratemap[ses[0].id], ratemap_rotate1)[0,1])
            ratemap_rotate2 = np.concatenate((self.ratemap[ses[4].id][i:],self.ratemap[ses[4].id][:i]))
            rotational_corrcoef2.append(np.corrcoef(self.ratemap[ses[2].id], ratemap_rotate2)[0,1])
        rotational_corrcoef1 = np.array(rotational_corrcoef1)
        rotational_corrcoef2 = np.array(rotational_corrcoef2)

        ax3 = fig.add_subplot(133)
        x = np.linspace(0, 360, num=int(nspatial_bins/bin_increment), endpoint=False)
        ax3.plot(x, rotational_corrcoef1, c='black')
        ax3.plot(x, rotational_corrcoef2, c='orange')
        ax3.plot([180,180], [-0.2,1], linestyle='dashed', c='grey')
        ax3.plot(x, [0.6]*np.size(x), c='red')
        
        a1 = np.where(rotational_corrcoef1 == np.max(rotational_corrcoef1))[0][0]*bin_increment
        a2 = np.where(rotational_corrcoef2 == np.max(rotational_corrcoef2))[0][0]*bin_increment
        return a1, a2


        

                    
                
            

            



