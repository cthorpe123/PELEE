import math
import numpy as np
from numu_tki import tki_calculators

# Selection Algorithms for the 1muNp channel
# Re-using selection developed by Steven Gardiner
# Author: C Thorpe

TRACK_SCORE_CUT = 0.5

MUON_P_MIN_MOM_CUT = 0.100
MUON_P_MAX_MOM_CUT = 1.200

LEAD_P_MIN_MOM_CUT = 0.250
LEAD_P_MAX_MOM_CUT = 1.

################################################################################
# Fiducial volume cut is already applied by preselection filter - repeated here
# for completeness

def sel_reco_vertex_in_FV(reco_nu_vtx_sce_x,reco_nu_vtx_sce_y,reco_nu_vtx_sce_z):
    
    return reco_nu_vtx_sce_x > 5.0 and reco_nu_vtx_sce_x < 251.0 and\
           abs(reco_nu_vtx_sce_y) < 111.0 and\
           reco_nu_vtx_sce_z > 20.0 and reco_nu_vtx_sce_z < 986.0 and\
           not (reco_nu_vtx_sce_z > 675 and reco_nu_vtx_sce_z < 775) 

################################################################################
# Point located in proton containment volume

PCV_X_MIN =   10.
PCV_X_MAX =  246.35
PCV_Y_MIN = -106.5
PCV_Y_MAX =  106.5
PCV_Z_MIN =   10.
PCV_Z_MAX = 1026.8

def in_proton_containment_vol(x,y,z):
    
    return x > PCV_X_MIN and x < PCV_X_MAX and\
           y > PCV_Y_MIN and y < PCV_Y_MAX and\
           z > PCV_Z_MIN and z < PCV_Z_MAX

################################################################################
# Make vector indicating if tracks are in the containedment volume 
def is_contained(track_end_sce_x_v,track_end_sce_y_v,track_end_sce_z_v):

    contained = []
    for i in range(0,len(track_end_sce_x_v)):
         contained.append(in_proton_containment_vol(track_end_sce_x_v[i],track_end_sce_y_v[i],track_end_sce_z_v[i]))

    return contained

################################################################################
# Apply generic numu cc selection

TOPOLOGICAL_SCORE_CUT=0.1

def pass_numu_CC_selection(topological_score,pfp_generation_v,track_start_sce_x_v,track_start_sce_y_v,track_start_sce_z_v,MuonCandidateIdx1muNp):
    
    if topological_score > TOPOLOGICAL_SCORE_CUT: return False
       
    sel_pfp_starts_in_PCV = True;
    
    for i in range(0,len(pfp_generation_v)):
        if pfp_generation_v[i] != 2: continue         
        sel_pfp_starts_in_PCV = in_proton_containment_vol(track_start_sce_x_v[i],track_start_sce_y_v[i],track_start_sce_z_v[i]) and sel_pfp_starts_in_PCV                
 
    if sel_pfp_starts_in_PCV == False: return False

    return MuonCandidateIdx1muNp != -1

################################################################################

MUON_TRACK_SCORE_CUT = 0.8
MUON_VTX_DISTANCE_CUT = 4.
MUON_LENGTH_CUT = 10.
MUON_PID_CUT = 0.2

def find_muon_candidate(pfp_generation_v,trk_score_v,trk_distance_v,trk_len_v,trk_llr_pid_score_v):
   
    index=-1
    highest_score=-1000  
    for i in range(0,len(pfp_generation_v)):
        if pfp_generation_v[i] != 2 or trk_score_v[i] < MUON_TRACK_SCORE_CUT or\
           trk_distance_v[i] > MUON_VTX_DISTANCE_CUT or trk_len_v[i] < MUON_LENGTH_CUT or\
           trk_llr_pid_score_v[i] < MUON_PID_CUT: continue   
        if trk_llr_pid_score_v[i] > highest_score:
            index=i
            highest_score=trk_llr_pid_score_v[i] 

    return index

################################################################################
# Get number of reconstructed showers 

def sel_reco_showers(pfp_generation_v,trk_score_v):
    showers=0
    for i in range(0,len(pfp_generation_v)):
        if pfp_generation_v[i] == 2 and trk_score_v[i] < TRACK_SCORE_CUT: showers=showers+1
    
    return showers 

################################################################################
# Check muon track is contained

def is_muon_contianed(MuonCandidateIdx_1muNp,IsContained_1muNp):
    return IsContained_1muNp[MuonCandidateIdx_1muNp]

################################################################################
# Get momentum of reconstructed muon track

def get_reco_muon_mom(MuonCandidateIdx_1muNp,trk_range_muon_mom_v,trk_mcs_muon_mom_v,MuonContained_1muNp):

    if MuonCandidateIdx_1muNp == -1: return np.nan

    if MuonContained_1muNp: return trk_range_muon_mom_v[MuonCandidateIdx_1muNp]
    else: return trk_mcs_muon_mom_v[MuonCandidateIdx_1muNp] 

################################################################################
# Get a component of the muon momentum 

def get_reco_muon_mom_comp(MuonCandidateIdx_1muNp,trk_range_muon_mom_v,trk_mcs_muon_mom_v,MuonContained_1muNp,trk_dir_v):

    if MuonCandidateIdx_1muNp == -1: return np.nan

    if MuonContained_1muNp: return trk_range_muon_mom_v[MuonCandidateIdx_1muNp]*trk_dir_v[MuonCandidateIdx_1muNp]
    else: return trk_mcs_muon_mom_v[MuonCandidateIdx_1muNp]*trk_dir_v[MuonCandidateIdx_1muNp] 

################################################################################
# Get energy of reconstructed muon track

MASS_MUON = 0.1057

def get_reco_muon_E(RecoMuonMomentum_1muNp):
    return math.sqrt(RecoMuonMomentum_1muNp*RecoMuonMomentum_1muNp + MASS_MUON*MASS_MUON) 

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

MASS_PROTON = 0.93827

def get_reco_proton_mom(LeadProtonIdx_1muNp,trk_energy_proton_v):

    ke = trk_energy_proton_v[LeadProtonIdx_1muNp]
    return math.sqrt(ke*ke + 2*MASS_PROTON*ke)

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

def get_reco_proton_mom_comp(LeadProtonIdx_1muNp,trk_energy_proton_v,trk_dir_v):

    if LeadProtonIdx_1muNp == -1: return np.nan

    ke = trk_energy_proton_v[LeadProtonIdx_1muNp]
    return math.sqrt(ke*ke + 2*MASS_PROTON*ke)*trk_dir_v[LeadProtonIdx_1muNp]

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

MASS_PROTON = 0.93827

def get_reco_proton_E(RecoLeadProtonMomentum_1muNp):

    return math.sqrt(RecoLeadProtonMomentum_1muNp*RecoLeadProtonMomentum_1muNp + MASS_PROTON*MASS_PROTON) 

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

MASS_PROTON = 0.93827

def get_reco_proton_E_v(RecoProtonMomentum_1muNp):

    E = []
    for i in range(0,len(RecoProtonMomentum_1muNp)):
        E.append(math.sqrt(RecoProtonMomentum_1muNp*RecoProtonMomentum_1muNp + MASS_PROTON*MASS_PROTON)) 

    return E

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

def get_reco_proton_mom_v(ProtonCandidateIdx_1muNp,trk_energy_proton_v):

    mom = []
    for i in range(0,len(ProtonCandidateIdx_1muNp)):
        ke = trk_energy_proton_v[ProtonCandidateIdx_1muNp[i]]
        mom.append(math.sqrt(ke*ke + 2*MASS_PROTON*ke))

    return mom

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

def get_reco_proton_mom_comp_v(ProtonCandidateIdx_1muNp,trk_energy_proton_v,trk_dir_v):

    mom = []
    for i in range(0,len(ProtonCandidateIdx_1muNp)):
        ke = trk_energy_proton_v[ProtonCandidateIdx_1muNp[i]]
        mom.append(math.sqrt(ke*ke + 2*MASS_PROTON*ke)*trk_dir_v[ProtonCandidateIdx_1muNp[i]])

    return mom

################################################################################
# Get momentum of reconstructed protons. Returns either a vector or 

MASS_PROTON = 0.93827

def get_reco_proton_E_v(RecoProtonMomentum_1muNp):

    E = []
    for i in range(0,len(RecoProtonMomentum_1muNp)):
        E.append(math.sqrt(RecoProtonMomentum_1muNp[i]*RecoProtonMomentum_1muNp[i] + MASS_PROTON*MASS_PROTON)) 

    return E

################################################################################
# Muon track momentun cuts 

def pass_mom_cut(RecoMuonMomentum_1muNp,CUT_LOW,CUT_HIGH):
    return RecoMuonMomentum_1muNp > CUT_LOW and RecoMuonMomentum_1muNp < CUT_HIGH 

################################################################################
# Check selected muon candidate passes momentum consistency check

MUON_MOM_QUALITY_CUT = 0.25 

def pass_muon_qual_cut(MuonCandidateIdx_1muNp,trk_range_muon_mom_v,trk_mcs_muon_mom_v):
    return abs(trk_range_muon_mom_v[MuonCandidateIdx_1muNp] - trk_mcs_muon_mom_v[MuonCandidateIdx_1muNp])/trk_range_muon_mom_v[MuonCandidateIdx_1muNp] < MUON_MOM_QUALITY_CUT

################################################################################
# Make a list of the indices of the protons candidates

DEFAULT_PROTON_PID_CUT = 0.2

def find_proton_candidates(MuonCandidateIdx_1muNp,pfp_generation_v,trk_score_v,trk_len_v,trk_llr_pid_score_v,IsContained_1muNp):

    proton_candidate_idx=[]
    for i in range(0,len(pfp_generation_v)):
        if pfp_generation_v[i] != 2 or i == MuonCandidateIdx_1muNp or\
           trk_score_v[i] < TRACK_SCORE_CUT or trk_len_v[i] < 0.0 or\
           trk_llr_pid_score_v[i] > DEFAULT_PROTON_PID_CUT or\
           not IsContained_1muNp[i]: continue
        
        proton_candidate_idx.append(i) 

    return proton_candidate_idx

################################################################################

def find_leading_proton_candidate(ProtonCandidateIdx_1muNp,trk_len_v):
    
    longest_idx=-1
    longest_len=-1
    for i in range(0,len(trk_len_v)):
        if i in ProtonCandidateIdx_1muNp and trk_len_v[i] > longest_len:
            longest_idx = i
            longest_len = trk_len_v[i]

    return longest_idx

################################################################################
# Apply the whole selection

def is_sel_1muNp(PassNuMuCCSelection_1muNp,NoRecoShowers_1muNp,MuonContained_1muNp,PassMuonMomentumCut_1muNp,PassMuonQualCut_1muNp,LeadProtonPassMomentumCut_1muNp):
    return PassNuMuCCSelection_1muNp and NoRecoShowers_1muNp and MuonContained_1muNp and\
           PassMuonMomentumCut_1muNp and PassMuonQualCut_1muNp and LeadProtonPassMomentumCut_1muNp

################################################################################
# Add a column to the dataframe indicating whether event passed the 1muNp selection

def apply_selection_1muNp(df,filter=False):
    print("Applying SG's selection")
    print(len(df))

    df["MuonCandidateIdx_1muNp"] = df.apply(lambda x: (find_muon_candidate(x["pfp_generation_v"],x["trk_score_v"],x["trk_distance_v"],x["trk_len_v"],x["trk_llr_pid_score_v"])),axis=1)
    if filter: df = df.query("MuonCandidateIdx_1muNp != -1")
  
    df["IsContained_1muNp"] = df.apply(lambda x: (is_contained(x["trk_sce_end_x_v"],x["trk_sce_end_y_v"],x["trk_sce_end_z_v"])),axis=1)
    df["PassNuMuCCSelection_1muNp"] = df.apply(lambda x: (pass_numu_CC_selection(x["topological_score"],x["pfp_generation_v"],x["trk_sce_start_x_v"],x["trk_sce_start_y_v"],x["trk_sce_start_z_v"],x["MuonCandidateIdx_1muNp"])),axis=1)
    if filter: df = df.query("PassNuMuCCSelection_1muNp == True")    

    df["NoRecoShowers_1muNp"] = df.apply(lambda x: (sel_reco_showers(x["pfp_generation_v"],x["trk_score_v"]) == 0),axis=1)
    if filter: df = df.query("NoRecoShowers_1muNp == True")

    df["MuonContained_1muNp"] = df.apply(lambda x: (is_muon_contianed(x["MuonCandidateIdx_1muNp"],x["IsContained_1muNp"])),axis=1)
    df["RecoMuonMomentum_1muNp"] = df.apply(lambda x: (get_reco_muon_mom(x["MuonCandidateIdx_1muNp"],x["trk_range_muon_mom_v"],x["trk_mcs_muon_mom_v"],x["MuonContained_1muNp"])),axis=1)
    df["PassMuonMomentumCut_1muNp"] = df.apply(lambda x: (pass_mom_cut(x["RecoMuonMomentum_1muNp"],MUON_P_MIN_MOM_CUT,MUON_P_MAX_MOM_CUT)),axis=1) 
    if filter: df = df.query("PassMuonMomentumCut_1muNp == True")

    df["PassMuonQualCut_1muNp"] = df.apply(lambda x: (pass_muon_qual_cut(x["MuonCandidateIdx_1muNp"],x["trk_range_muon_mom_v"],x["trk_mcs_muon_mom_v"])),axis=1)
    if filter: df = df.query("PassMuonQualCut_1muNp == True")

    df["ProtonCandidateIdx_1muNp"] = df.apply(lambda x: (find_proton_candidates(x["MuonCandidateIdx_1muNp"],x["pfp_generation_v"],x["trk_score_v"],x["trk_len_v"],x["trk_llr_pid_score_v"],x["IsContained_1muNp"])),axis=1)
    
    df["LeadProtonIdx_1muNp"] = df.apply(lambda x: (find_leading_proton_candidate(x["ProtonCandidateIdx_1muNp"],x["trk_len_v"])),axis=1)
    df["RecoLeadProtonMomentum_1muNp"] = df.apply(lambda x: (get_reco_proton_mom(x["LeadProtonIdx_1muNp"],x["trk_energy_proton_v"])),axis=1)
    df["RecoProtonMomentum_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_v(x["ProtonCandidateIdx_1muNp"],x["trk_energy_proton_v"])),axis=1)
    df["LeadProtonPassMomentumCut_1muNp"] = df.apply(lambda x: (pass_mom_cut(x["RecoLeadProtonMomentum_1muNp"],LEAD_P_MIN_MOM_CUT,LEAD_P_MAX_MOM_CUT)),axis=1)
    if filter: df = df.query("LeadProtonPassMomentumCut_1muNp == True")  

    df["sel_CCNp0pi"] = df.apply(lambda x: (is_sel_1muNp(x["PassNuMuCCSelection_1muNp"],x["NoRecoShowers_1muNp"],x["MuonContained_1muNp"],x["PassMuonMomentumCut_1muNp"],x["PassMuonQualCut_1muNp"],x["LeadProtonPassMomentumCut_1muNp"])),axis=1)
    if filter: df = df.query("sel_CCNp0pi == True")

     # If the event passes the selection, set the various momentum/tki variables     
    df["RecoMuonE_1muNp"] = df.apply(lambda x: (get_reco_muon_E(x["RecoMuonMomentum_1muNp"])),axis=1)
    df["RecoMuonMomX_1muNp"] = df.apply(lambda x: (get_reco_muon_mom_comp(x["MuonCandidateIdx_1muNp"],x["trk_range_muon_mom_v"],x["trk_mcs_muon_mom_v"],x["MuonContained_1muNp"],x["trk_dir_x_v"])),axis=1)
    df["RecoMuonMomY_1muNp"] = df.apply(lambda x: (get_reco_muon_mom_comp(x["MuonCandidateIdx_1muNp"],x["trk_range_muon_mom_v"],x["trk_mcs_muon_mom_v"],x["MuonContained_1muNp"],x["trk_dir_y_v"])),axis=1)
    df["RecoMuonMomZ_1muNp"] = df.apply(lambda x: (get_reco_muon_mom_comp(x["MuonCandidateIdx_1muNp"],x["trk_range_muon_mom_v"],x["trk_mcs_muon_mom_v"],x["MuonContained_1muNp"],x["trk_dir_z_v"])),axis=1)

    df["RecoLeadProtonE_1muNp"] = df.apply(lambda x: (get_reco_proton_E(x["RecoLeadProtonMomentum_1muNp"])),axis=1)
    df["RecoLeadProtonMomX_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_comp(x["LeadProtonIdx_1muNp"],x["trk_energy_proton_v"],x["trk_dir_x_v"])),axis=1)
    df["RecoLeadProtonMomY_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_comp(x["LeadProtonIdx_1muNp"],x["trk_energy_proton_v"],x["trk_dir_y_v"])),axis=1)
    df["RecoLeadProtonMomZ_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_comp(x["LeadProtonIdx_1muNp"],x["trk_energy_proton_v"],x["trk_dir_z_v"])),axis=1)

    df["RecoProtonE_1muNp"] = df.apply(lambda x: (get_reco_proton_E_v(x["RecoProtonMomentum_1muNp"])),axis=1)
    df["RecoProtonMomX_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_comp_v(x["ProtonCandidateIdx_1muNp"],x["trk_energy_proton_v"],x["trk_dir_x_v"])),axis=1)
    df["RecoProtonMomY_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_comp_v(x["ProtonCandidateIdx_1muNp"],x["trk_energy_proton_v"],x["trk_dir_y_v"])),axis=1)
    df["RecoProtonMomZ_1muNp"] = df.apply(lambda x: (get_reco_proton_mom_comp_v(x["ProtonCandidateIdx_1muNp"],x["trk_energy_proton_v"],x["trk_dir_z_v"])),axis=1)

    # Drop all of the temporary columns added to the dataframe to save space
    df.drop("MuonCandidateIdx_1muNp",inplace=True,axis=1) 
    df.drop("IsContained_1muNp",inplace=True,axis=1) 
    df.drop("PassNuMuCCSelection_1muNp",inplace=True,axis=1)
    df.drop("NoRecoShowers_1muNp",inplace=True,axis=1)
    df.drop("MuonContained_1muNp",inplace=True,axis=1)
    df.drop("PassMuonMomentumCut_1muNp",inplace=True,axis=1)
    df.drop("PassMuonQualCut_1muNp",inplace=True,axis=1)
    df.drop("ProtonCandidateIdx_1muNp",inplace=True,axis=1) 
    df.drop("LeadProtonIdx_1muNp",inplace=True,axis=1)
    df.drop("LeadProtonPassMomentumCut_1muNp",inplace=True,axis=1)
   
    print("Calc reco TKI variables for leading proton only")

    df["RecoDeltaPT_1mu1p"] = df.apply(lambda x: (tki_calculators.delta_pT(x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaPhiT_1mu1p"] = df.apply(lambda x: (tki_calculators.delta_phiT(x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaAlphaT_1mu1p"] = df.apply(lambda x: (tki_calculators.delta_alphaT(x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoECal_1mu1p"] = df.apply(lambda x: (tki_calculators.Ecal(x["RecoMuonE_1muNp"],x["RecoLeadProtonE_1muNp"])),axis=1)
    df["RecoPL_1mu1p"] = df.apply(lambda x: (tki_calculators.pL(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoPN_1mu1p"] = df.apply(lambda x: (tki_calculators.pn(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoAlpha3D_1mu1p"] = df.apply(lambda x: (tki_calculators.alpha_3D(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoPhi3D_1mu1p"] = df.apply(lambda x: (tki_calculators.phi_3D(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaPTX_1mu1p"] = df.apply(lambda x: (tki_calculators.delta_pT_X(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaPTY_1mu1p"] = df.apply(lambda x: (tki_calculators.delta_pT_Y(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoPNTX_1mu1p"] = df.apply(lambda x: (tki_calculators.pn_TX(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoPNTY_1mu1p"] = df.apply(lambda x: (tki_calculators.pn_TY(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoPNT_1mu1p"] = df.apply(lambda x: (tki_calculators.pn_T(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)
    df["RecoPNII_1mu1p"] = df.apply(lambda x: (tki_calculators.pn_II(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoLeadProtonE_1muNp"],x["RecoLeadProtonMomX_1muNp"],x["RecoLeadProtonMomY_1muNp"],x["RecoLeadProtonMomZ_1muNp"])),axis=1)

    print("Calc reco TKI variables with all FS protons above threshold")

    df["RecoDeltaPT_1muNp"] = df.apply(lambda x: (tki_calculators.delta_pT(x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaPhiT_1muNp"] = df.apply(lambda x: (tki_calculators.delta_phiT(x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaAlphaT_1muNp"] = df.apply(lambda x: (tki_calculators.delta_alphaT(x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoECal_1muNp"] = df.apply(lambda x: (tki_calculators.Ecal(x["RecoMuonE_1muNp"],x["RecoProtonE_1muNp"])),axis=1)
    df["RecoPL_1muNp"] = df.apply(lambda x: (tki_calculators.pL(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoPN_1muNp"] = df.apply(lambda x: (tki_calculators.pn(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoAlpha3D_1muNp"] = df.apply(lambda x: (tki_calculators.alpha_3D(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoPhi3D_1muNp"] = df.apply(lambda x: (tki_calculators.phi_3D(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaPTX_1muNp"] = df.apply(lambda x: (tki_calculators.delta_pT_X(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoDeltaPTY_1muNp"] = df.apply(lambda x: (tki_calculators.delta_pT_Y(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoPNTX_1muNp"] = df.apply(lambda x: (tki_calculators.pn_TX(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoPNTY_1muNp"] = df.apply(lambda x: (tki_calculators.pn_TY(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoPNT_1muNp"] = df.apply(lambda x: (tki_calculators.pn_T(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)
    df["RecoPNII_1muNp"] = df.apply(lambda x: (tki_calculators.pn_II(x["RecoMuonE_1muNp"],x["RecoMuonMomX_1muNp"],x["RecoMuonMomY_1muNp"],x["RecoMuonMomZ_1muNp"],x["RecoProtonE_1muNp"],x["RecoProtonMomX_1muNp"],x["RecoProtonMomY_1muNp"],x["RecoProtonMomZ_1muNp"])),axis=1)


    df.drop("RecoProtonE_1muNp",inplace=True,axis=1)
    df.drop("RecoProtonMomentum_1muNp",inplace=True,axis=1)
    df.drop("RecoProtonMomX_1muNp",inplace=True,axis=1)
    df.drop("RecoProtonMomY_1muNp",inplace=True,axis=1)
    df.drop("RecoProtonMomZ_1muNp",inplace=True,axis=1)
   
    return df
