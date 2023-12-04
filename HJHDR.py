# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 13:31:54 2023

@author: Junhao
"""

from NCP import *



fdir = Path(r'H:\Filez\HJH\2312')
fn = '2312-1124-dr'
# by experiment_tag, you can customize alot in your functions without interference with others'. 
experiment_tag = {'Nses':9,
                  'theme':'spatial',
                  'maze shape':'circular',
                  'experiment':'DR',
                  'signal':'inhibitory tagging',
                  'multi tagging session':{},
                  'video record mode':'Bonsai',
                  'extract waveforms':True,
                  'sync_rate':2,
                  'sample_rate':30000,
                  'fontsize':15}
dlc_col_ind_dict = {'left_pos':0, 'right_pos':3}

spike_clusters, timestamps, clusters_info, vsync, esync_timestamps, dlc_files, frame_state, extra = load_files(fdir,fn,experiment_tag,dlc_tail='DLC_resnet50_HPC_DRJun4shuffle1_280000_filtered.h5')

sync_check(esync_timestamps, vsync, experiment_tag)
# if you find sth. wrong, pause here and check your e-v sync data.

#%% if you need to correct your sync variables.
# esync_timestamps[0] = esync_timestamps[0][2:]#for 2312-1127-dr
# esync_timestamps[1] = esync_timestamps[1][1:]#for 2312-1127-dr
# esync_timestamps[3] = esync_timestamps[3][1:]#for 2312-1127-dr

# esync_timestamps[2] = esync_timestamps[2][4:]
# esync_timestamps[4] = esync_timestamps[4][2:]
# esync_timestamps[1] = np.append(esync_timestamps[1], esync_timestamps[1][-1]+ 14998)
sync_check(esync_timestamps, vsync, experiment_tag)
extra['signal_on_timestamps'][7] = extra['signal_on_timestamps'][7][:-2]#for 2312-1124-dr
#%% TEST extract waveforms.
# c = np.load(r'F:\KiloSortTemp\2312-1124-dr\_phy_spikes_subset.waveforms.npy')
# a = np.load(r'F:\KiloSortTemp\2312-1124-dr\_phy_spikes_subset.spikes.npy')
# d = np.load(r'F:\KiloSortTemp\2312-1124-dr\spike_times.npy')
# e = np.load(r'F:\KiloSortTemp\2312-1124-dr\spike_clusters.npy')
# a1 = e[a]
# # c1 = c[:,11:71,:]
# a = extra['waveforms'][np.where(extra['waveforms clusters'] == 138)]
# b = np.mean(a, axis=0)
# c = b[:,:4]
# x = np.arange(c.shape[0])
# fig, ax=plt.subplots(2,2, sharex='all',sharey='all')
# ax[0,0].plot(x,c[:,0])
# ax[0,1].plot(x,c[:,1])
# ax[1,0].plot(x,c[:,2])
# ax[1,1].plot(x,c[:,3])


# a = esync_timestamps[7]
# b = np.delete(extra['waveforms'], np.where(extra['waveforms timestamps'] > a[-1]), axis=0)
# b = np.delete(b, np.where(extra['waveforms timestamps'] < a[0]), axis=0)
# c = np.delete(extra['waveforms clusters'], np.where(extra['waveforms timestamps'] > a[-1]), axis=0)
# c = np.delete(c, np.where(extra['waveforms timestamps'] < a[0]), axis=0)
#%% ANALYSIS
# after esync_timestamps is corrected

    

uall_posi = []
uall_nega = []
units = []
if experiment_tag['Nses'] == 1:
    raise Exception('WOW got alot to check.')
#     ses1 = DRsession(dlc_files, dlc_col_ind_dict, vsync, sync_rate, experiment_tag)
#     ses1.sync_cut_generate_frame_time()
#     ses1.remove_nan_merge_pos_get_hd()
#     ses1.generate_time2xy_interpolate(mode='cspline')
#     ses1.generate_spd_mask_20ms_bin() 
#     ses1.generate_dwell_map_circular()

#     t = time.time()
#     spike_pack = sync_cut_stamps2time(spike_clusters, timestamps, ses1, esync_timestamps, sync_rate, experiment_tag)
#     spike_pack = apply_spd_mask_20msbin(spike_pack[0], spike_pack[1], spike_pack[2], ses, temporal_bin_length=0.02)
#     print(time.time() -t, 'sec')


#     for i in range(0, clusters_quality.shape[0]):
#         if clusters_quality.loc[i,'group'] != 'noise':#if you have not mannually save your decision, then the col name is 'KSLabel'
#             unit_load = Unit1DCircular(clusters_quality.loc[i, 'cluster_id'],
#                              spike_pack,
#                              clusters_quality.loc[i, 'group'],#                              Nses,
#                              experiment_tag,
#                              fontsize)
#             unit_load.get_ratemap_1d_circular(ses1)
#             unit_load.get_stability_1d_circular(ses1)
#             unit_load.get_spatial_info_Skaggs(ses1) 
#             unit_load.get_positional_info_Olyper(ses1)
#             unit_load.simple_putative_IN_PC_by_firingrate(ses1)
#             # if unit_load.quality == 'good':
#             #     SUA.append(unit_load)
#             # elif unit_load.quality == 'mua':
#             #     MUA.append(unit_load)
#             units.append(unit_load)


elif experiment_tag['Nses'] > 1:
    spike_packages = []
    for i in range(experiment_tag['Nses']):
        t = time.time()
        exec('ses{0} = DRsession(dlc_files[{1}], dlc_col_ind_dict, vsync[{1}], experiment_tag, ses_id={1})'.format(i+1,i))
        exec('ses{}.sync_cut_generate_frame_time()'.format(i+1))
        exec('ses{}.remove_nan_merge_pos_get_hd()'.format(i+1))
        exec('ses{}.generate_time2xy_interpolate()'.format(i+1))
        exec('ses{}.generate_spd_mask_20ms_bin()'.format(i+1))
        exec('ses{}.generate_dwell_map_circular()'.format(i+1))
        exec('spike_pack = sync_cut_stamps2time(spike_clusters[{0}], timestamps[{0}], ses{1}, esync_timestamps[{0}], experiment_tag)'.format(i,i+1))
        exec('spike_pack = apply_spd_mask_20msbin(spike_pack[0], spike_pack[1], spike_pack[2], ses{}, experiment_tag)'.format(i+1))
        spike_packages.append(spike_pack)
        print(time.time() -t, 'sec for ses',(i+1))
        
        
if 'signal' in experiment_tag.keys():
    extra['signal_on_time'] = signal_stamps2time(esync_timestamps, extra['signal_on_timestamps'], experiment_tag)
    if experiment_tag['extract waveforms'] == True:
        extra['wavefroms right tagging'] = get_all_mean_waveforms_session(extra, ses8, esync_timestamps)
        extra['wavefroms left tagging'] = get_all_mean_waveforms_session(extra, ses9, esync_timestamps)


    uall_posi = []
    uall_nega = []
    units = []
    for i in range(0, clusters_info.shape[0]):
        if clusters_info.loc[i,'group'] is not np.nan and clusters_info.loc[i,'group'] != 'noise':#if you have not mannually save your decision, then the col name is 'KSLabel'
            unit_load = Unit1DCircular(spike_packages, clusters_info.iloc[i], experiment_tag)
            for ii in range(experiment_tag['Nses']):
                exec('unit_load.get_ratemap_1d_circular(ses'+str(ii+1)+')')
                exec('unit_load.get_stability_1d_circular(ses'+str(ii+1)+')')
                exec('unit_load.get_spatial_info_Skaggs(ses'+str(ii+1)+')')
                exec('unit_load.get_positional_info_Olyper(ses'+str(ii+1)+')')
                
            if unit_load.loc < 32:
                unit_load.loc = 'right'
            else:
                unit_load.loc = 'left'
            unit_load.get_mean_waveforms(extra)
            unit_load.get_mean_waveforms_tagging(extra)
            unit_load.simple_is_place_cell_DR()
            unit_load.simple_putative_IN_PC_by_firingrate(ses=[ses1,ses2,ses3,ses4,ses5])#distinguish PC and IN.
            unit_load.opto_inhibitory_tagging([ses8,ses9], extra['signal_on_time'], mode='ranksum', check_waveforms=True)#Opto tag.
            unit_load.DR_standard_check([ses1,ses2,ses3,ses8,ses9], ['k','grey','b','r','orange','orange'], save=(fdir,fn))
            unit_load.plot_ratemap_and_rotational_corr([ses4,ses5,ses6,ses7,ses8],
                                                        conflict_ses=[5,7], legend_list=['std1', '135', 'std2', '90', 'tagging'],
                                                        signal_on_time=extra['signal_on_time'], signal_on_ses=[8,9], save = (fdir,fn))
            

            if unit_load.type == 'excitatory' and unit_load.opto_tag == 'positive':
                uall_posi.append(unit_load)
            elif unit_load.type == 'excitatory' and unit_load.opto_tag == 'negative':
                uall_nega.append(unit_load)
            units.append(unit_load)
#%% save pickle
ses = [ses1,ses2,ses3,ses4,ses5,ses6,ses7,ses8,ses9]
uall = [units, uall_posi, uall_nega]
with open(Path(r'H:\Filez\HJH')/(fn+'_13590'), 'wb') as f1:
    pickle.dump([ses, uall], f1)
f1.close()


#%% load pickle, check
with open(r'H:\Filez\HJH\', 'rb') as f1:
    a = pickle.load(f1)
f1.close()
#%%
for i in units:
    # print(i.spatial_info)
    # print(np.nanmax(i.positional_info))
    # i.plot_ratemap_1d_circular_polar(ses1)
    # i.plot_ratemap_1d_circular_polar([ses1,ses2,ses3,ses4,ses5])
    # i.plot_ratemap_and_rotational_corr([ses1,ses2,ses3,ses4,ses5])
    # i.raster_plot_peri_stimulus(ses5, signal_on_time[0])
    i.opto_inhibitory_tagging([ses8, ses9], extra['signal_on_time'], mode='ranksum', check_waveforms=True)#Opto tag.












    
    
    
#%% group analysis

from NCP import *
figpath = Path(r'H:\Filez\HJH\HJH2')
datapath = Path(r'H:\Filez\HJH')
with open(datapath/'2312-1124-dr_13590', 'rb') as f1:
    m231213590 = pickle.load(f1)
f1.close()
with open(datapath/'2312-1127-dr_45180', 'rb') as f1:
    m231245180 = pickle.load(f1)
f1.close()

#%% DR std check.
plt.rcParams['xtick.labelsize'] = 15
plt.rcParams['ytick.labelsize'] = 15

# for i in uall_230713545[0]:
#     i.simple_is_place_cell_DR()
#     i.plot_ratemap_and_rotational_corr(ses_230713545)
# #     i.DR_standard_check(ses_230345135)
#     i.plot_spike_position(ses_230713545)

data = m231213590

rotcorr1 = []
rotcorr2 = []
for i in data[1][0]:
    # i.fontsize = 10
    if any(i.is_place_cell) == True:
        a1, a2 = i.DR_standard_check(data[0][1:])
        rotcorr1.append(a1)
        rotcorr2.append(a2)
    else:
        pass
rotcorr1 = np.array(rotcorr1)
rotcorr2 = np.array(rotcorr2)
#% DR std check plot.
fig, axes = plt.subplots(2, 1, figsize=(7,12), layout='constrained')
axes[0].set_axis_off()#HAHAHAHAHAHA EVIL CODING
axes[0] = fig.add_subplot(2, 1, 1, projection='polar')
axes[0].set_title('rot. corr. of standard pair', fontsize=30)
axes[0].set_theta_direction('clockwise')
axes[0].set_theta_offset(np.pi/2)
axes[0].scatter(rotcorr1/180*np.pi, 5+np.random.ranf(np.size(rotcorr1)), c='grey', s=300,alpha=0.8)
axes[0].scatter(rotcorr2/180*np.pi, 5+np.random.ranf(np.size(rotcorr1)), c='orange', s=300,alpha=0.8)

axes[1].hist(rotcorr1, bins=18, color='grey', alpha=0.7)
axes[1].hist(rotcorr2, bins=18, color='orange', alpha=0.7)
axes[1].set_xlabel('degrees of rotation', fontsize=20)
axes[1].set_ylabel('N of standard pairs', fontsize=20)





#%% basic params.
posi_all = []
nega_all = []
posi_all.extend(m231213590[1][1])
posi_all.extend(m231245180[1][1])
nega_all.extend(m231213590[1][2])
nega_all.extend(m231245180[1][2])

c45 = [[],[]]
c90 = [[],[]]
c135 = [[],[]]
c180 = [[],[]]
for i in m231213590[1][1]:
    if i.rotational_correlation_peak[0] is not False:    
        c135[0].append(i.rotational_correlation_peak[0])
    if i.rotational_correlation_peak[1] is not False:    
        c90[0].append(i.rotational_correlation_peak[1])
for i in m231213590[1][2]:
    if i.rotational_correlation_peak[0] is not False:    
        c135[1].append(i.rotational_correlation_peak[0])
    if i.rotational_correlation_peak[1] is not False:    
        c90[1].append(i.rotational_correlation_peak[1])
for i in m231245180[1][1]:
    if i.rotational_correlation_peak[0] is not False:    
        c45[0].append(i.rotational_correlation_peak[0])
    if i.rotational_correlation_peak[1] is not False:    
        c180[0].append(i.rotational_correlation_peak[1])
for i in m231245180[1][2]:
    if i.rotational_correlation_peak[0] is not False:    
        c45[1].append(i.rotational_correlation_peak[0])
    if i.rotational_correlation_peak[1] is not False:    
        c180[1].append(i.rotational_correlation_peak[1])

    
#%%
for i in m231090135[1][1]:
    print(i.rotational_correlation_peak)
    

#%% get pos. & spa. info.
posi_spainfo = []# all max in all five ses
posi_posinfo = []
posi_peakrate = []
nega_spainfo = []
nega_posinfo = []
nega_peakrate = []
for i in posi_all:
    # if np.max(np.array(i.spatial_info))>1 or np.max(np.array((np.nanmax(i.positional_info[0]),np.nanmax(i.positional_info[1]),np.nanmax(i.positional_info[2]),np.nanmax(i.positional_info[3]),np.nanmax(i.positional_info[4]))))>0.8:
    if any(i.is_place_cell) == True:
        posi_spainfo.append(np.max(np.array(i.spatial_info)))
        posi_posinfo.append(np.max(np.array((np.nanmax(i.positional_info[0]),np.nanmax(i.positional_info[1]),np.nanmax(i.positional_info[2]),np.nanmax(i.positional_info[3]),np.nanmax(i.positional_info[4])))))
        posi_peakrate.append(np.max(np.array(i.peakrate)))
for ii in nega_all:
    # if np.max(np.array(i.spatial_info))>1 or np.max(np.array((np.nanmax(i.positional_info[0]),np.nanmax(i.positional_info[1]),np.nanmax(i.positional_info[2]),np.nanmax(i.positional_info[3]),np.nanmax(i.positional_info[4]))))>0.8:
    if any(ii.is_place_cell) == True:
        nega_spainfo.append(np.max(np.array(ii.spatial_info)))
        nega_posinfo.append(np.max(np.array((np.nanmax(ii.positional_info[0]),np.nanmax(ii.positional_info[1]),np.nanmax(ii.positional_info[2]),np.nanmax(ii.positional_info[3]),np.nanmax(ii.positional_info[4])))))
        nega_peakrate.append(np.max(np.array(ii.peakrate)))

posi_spainfo = np.array(posi_spainfo)# all max in all five ses
posi_posinfo = np.array(posi_posinfo)
posi_peakrate = np.array(posi_peakrate)
nega_spainfo = np.array(nega_spainfo)
nega_posinfo = np.array(nega_posinfo)
nega_peakrate = np.array(nega_peakrate)
    
 
#%% basic plots
fig = plt.figure()
ax = fig.add_subplot(111)
x1 = 1.5 + np.random.ranf(np.size(nega_spainfo))
x2 = 4.5 + np.random.ranf(np.size(posi_spainfo))
ax.set_title('Peak Firing Rate', fontsize=20)
ax.scatter(x1, nega_peakrate, c='grey')
ax.scatter(x2, posi_peakrate, c='green')
ax.set_xticks([0,2,5,7])
ax.set_xticklabels(['','negative PC','positive PC',''], fontsize=15)
ax.set_ylabel('spikes per sec', fontsize=15)
fig.savefig(figpath/'peakrate.svg', format='svg', dpi=150)
# peakrate, ranksum, pvalue=0.0236104325888814
# after bar of is_place_cell, RanksumsResult(statistic=-3.293990613669936, pvalue=0.0009877579684642852)
#%%
fig = plt.figure()
ax = fig.add_subplot(111)
x1 = 1.5 + np.random.ranf(np.size(nega_spainfo))
x2 = 4.5 + np.random.ranf(np.size(posi_spainfo))
ax.set_title('Spatial Information', fontsize=20)
ax.scatter(x1, nega_spainfo, c='grey')
ax.scatter(x2, posi_spainfo, c='green')
ax.set_xticks([0,2,5,7])
ax.set_xticklabels(['','negative PC','positive PC',''], fontsize=15)
ax.set_ylabel('Bits per Spike', fontsize=15)
# after bar of is_place_cell pvalue=0.005646679424886402
fig.savefig(figpath/'spatialinfo.svg', format='svg', dpi=150)
#%%
fig = plt.figure()
ax = fig.add_subplot(111)
x1 = 1.5 + np.random.ranf(np.size(nega_posinfo))
x2 = 4.5 + np.random.ranf(np.size(posi_posinfo))
ax.set_title('Positional Information', fontsize=20)
ax.scatter(x1, nega_posinfo, c='grey')
ax.scatter(x2, posi_posinfo, c='green')
ax.set_xticks([0,2,5,7])
ax.set_xticklabels(['','negative PC','positive PC',''], fontsize=15)
ax.set_ylabel('Bits', fontsize=15)
fig.savefig(figpath/'positionalinfo.svg', format='svg', dpi=150)

#%%
p = np.array(c180[0])
n = np.array(c180[1])
bins = 18

fig = plt.figure(figsize=(7,7))
ax1 = fig.add_subplot(111, projection='polar')
# ax2 = fig.add_subplot(212)
ax1.set_theta_direction('clockwise')
ax1.set_theta_offset(np.pi/2)
ax1.scatter(n/180*np.pi, 7+np.random.ranf(np.size(n)), c='grey', s=300,alpha=0.7)
ax1.scatter(p/180*np.pi, 5+np.random.ranf(np.size(p)), c='green', s=300,alpha=0.7)
# ax2.hist(n, bins=bins, color='grey', alpha=0.7, histtype='bar')
# ax2.hist(p, bins=bins, color='green', alpha=0.5, histtype='bar')

# ax2.set_xlabel('degrees of rotation', fontsize=20)
# ax2.set_ylabel('Num of session pairs', fontsize=20)
# ax2.set_yticks([0,1,2,3,4,5,6,7])
ax1.set_title('pairs of 180 degree, N={},{}'.format(np.size(p),np.size(n)), fontsize=30)
fig.savefig(figpath/'conflict180.svg', format='svg', dpi=600)


#%% Charts
# posi_prop = [34,29,25,12,38,43,104]
# nega_prop = [21,15,14,6,15,18,40]
posi_prop = [34,29,25,12,38,43]
nega_prop = [21,15,14,6,15,18]
# fig = plt.figure(figsize=(20,10))
# ax1 = fig.add_subplot(121)
# ax2 = fig.add_subplot(122)
# ax1.pie(nega_prop)
# ax2.pie(posi_prop)
# ax2.set_label(['rotate','gain field','loss field','remap','non-spatial'])
plt.figure(figsize=(10,10))
plt.pie(x=posi_prop,
        labels=['distal cue dominant','local cue dominant','remap','stable field','gain field','loss field'],
        colors=['blue', 'orange', 'green','red','cyan','purple'],
        autopct='%.2f%%',
        textprops={'fontsize': 20},
        radius=1)
# plt.title('Positive PC session pairs')
# plt.show()
plt.savefig(figpath/'posi_pie2.svg', format='svg', dpi=600)















    
    
    
























