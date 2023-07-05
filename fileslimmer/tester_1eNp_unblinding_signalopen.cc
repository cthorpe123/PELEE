#include "Riostream.h"
// #include "TString.h"
// #include "TFile.h"
// #include "TTree.h"
#include <map>
#include <iostream>
#include <cstdlib>

void tester_1eNp_unblinding(TString fSIDEBAND, TString fBLIND)
{
  
  // Get SIDEBAND file & tree and set top branch address
  TFile SIDEBANDfile(fSIDEBAND);
  TTree *SIDEBANDtree;
  SIDEBANDfile.GetObject("nuselection/NeutrinoSelectionFilter", SIDEBANDtree);
  
  // Get BLIND file & tree and set top branch address
  TFile BLINDfile(fBLIND);
  TTree *BLINDtree;
  BLINDfile.GetObject("nuselection/NeutrinoSelectionFilter", BLINDtree);

  // number of entries passing in both files
  int far_sideband_SIDEBAND = 0;
  int far_sideband_BLIND = 0;
  
  
  const auto nentriesSIDEBAND = SIDEBANDtree->GetEntries();
  const auto nentriesBLIND    = BLINDtree->GetEntries();
  
  // Deactivate all branches
  SIDEBANDtree->SetBranchStatus("*", 1);
  BLINDtree->SetBranchStatus("*", 1);
  
  int backtracked_pdg;
  
  int run,sub,evt;
  int nslice;
  int selected;
  float shr_energy_tot_cali;
  float _opfilter_pe_beam;
  float _opfilter_pe_veto;
  uint n_tracks_contained;
  uint n_showers_contained;
  float bdt_bkg_0p, bdt_pi0_np, bdt_nonpi0_np;
  float reco_e;
  float contained_fraction;
  int n_showers;
  
  // maps linking run -> std::vector< event >
  std::map<int,std::vector<int>> SIDEBAND_PRESEL_MAP;
  std::map<int,std::vector<int>> SIDEBAND_FAR_MAP;
  
  SIDEBANDtree->SetBranchAddress("run", &run);
  SIDEBANDtree->SetBranchAddress("sub", &sub);
  SIDEBANDtree->SetBranchAddress("evt", &evt);
  SIDEBANDtree->SetBranchAddress("nslice", &nslice);
  SIDEBANDtree->SetBranchAddress("selected", &selected);
  SIDEBANDtree->SetBranchAddress("contained_fraction", &contained_fraction);
  SIDEBANDtree->SetBranchAddress("shr_energy_tot_cali", &shr_energy_tot_cali);
  SIDEBANDtree->SetBranchAddress("n_tracks_contained", &n_tracks_contained);
  SIDEBANDtree->SetBranchAddress("n_showers_contained", &n_showers_contained);
  SIDEBANDtree->SetBranchAddress("bdt_bkg_0p", &bdt_bkg_0p);
  SIDEBANDtree->SetBranchAddress("bdt_pi0_np", &bdt_pi0_np);
  SIDEBANDtree->SetBranchAddress("bdt_nonpi0_np", &bdt_nonpi0_np);
  SIDEBANDtree->SetBranchAddress("reco_e", &reco_e);
  SIDEBANDtree->SetBranchAddress("n_showers", &n_showers);
  
  std::cout << "Start loop with " << nentriesSIDEBAND << " of SIDEBAND file." << std::endl;
  
  for (auto i : ROOT::TSeqI(nentriesSIDEBAND)) {

    if (i % 10000 == 0)
      std::cout << "Entry num  " << i << std::endl;
    
    SIDEBANDtree->GetEntry(i);
    
    bool preseq = (nslice == 1) && (shr_energy_tot_cali > 0.07) && (contained_fraction > 0.9) && (n_showers_contained > 0) && (n_tracks_contained > 0) ;
    bool presel1eNp = preseq && (n_showers_contained == 1);
    
    bool low_pid = ((bdt_pi0_np > 0) && (bdt_pi0_np < 0.1)) || ((bdt_nonpi0_np > 0) && (bdt_nonpi0_np < 0.1));
    bool high_pid = ((bdt_pi0_np > 0.67) && (bdt_nonpi0_np > 0.70));
    bool high_energy = reco_e > 0.85;
    bool medium_energy = reco_e > 0.65;
    bool high_bdt = bdt_bkg_0p > 0.72;

    bool far_sideband = (low_pid || high_energy);
    bool signal_open = (high_pid && medium_energy);
    
    if (presel1eNp && signal_open) {

      far_sideband_SIDEBAND += 1;

      std::cout << "Run, Event "<< run << ", " << evt << " passes the 1eNp BDT selection for the (near+far) energy sideband in the SIDEBAND file." <<std::endl;
      
      if (SIDEBAND_FAR_MAP.find(run) == SIDEBAND_FAR_MAP.end()) {
	std::vector<int> evt_v = {evt};
	SIDEBAND_FAR_MAP[run] = evt_v;
      }
      else {
	SIDEBAND_FAR_MAP[run].push_back( evt );
      }
    }

  }// for all entries of SIDEBAND tree
  
  
  // maps linking run -> std::vector< event >
  std::map<int,std::vector<int>> BLIND_PRESEL_MAP;
  std::map<int,std::vector<int>> BLIND_FAR_MAP;
  
  BLINDtree->SetBranchAddress("run", &run);
  BLINDtree->SetBranchAddress("sub", &sub);
  BLINDtree->SetBranchAddress("evt", &evt);
  BLINDtree->SetBranchAddress("nslice", &nslice);
  BLINDtree->SetBranchAddress("selected", &selected);
  BLINDtree->SetBranchAddress("contained_fraction", &contained_fraction);
  BLINDtree->SetBranchAddress("shr_energy_tot_cali", &shr_energy_tot_cali);
  BLINDtree->SetBranchAddress("n_tracks_contained", &n_tracks_contained);
  BLINDtree->SetBranchAddress("n_showers_contained", &n_showers_contained);
  BLINDtree->SetBranchAddress("bdt_bkg_0p", &bdt_bkg_0p);
  BLINDtree->SetBranchAddress("bdt_pi0_np", &bdt_pi0_np);
  BLINDtree->SetBranchAddress("bdt_nonpi0_np", &bdt_nonpi0_np);
  BLINDtree->SetBranchAddress("reco_e", &reco_e);
  BLINDtree->SetBranchAddress("n_showers", &n_showers);


  std::cout << "Start loop with " << nentriesBLIND << " of BLIND file." << std::endl;
  
  for (auto i : ROOT::TSeqI(nentriesBLIND)) {

    if (i % 10000 == 0)
      std::cout << "Entry num  " << i << std::endl;
    
    BLINDtree->GetEntry(i);

    bool preseq = (nslice == 1) && (shr_energy_tot_cali > 0.07) && (contained_fraction > 0.9) && (n_showers_contained > 0) && (n_tracks_contained > 0) ;
    bool presel1eNp = preseq && (n_showers_contained == 1);
    
    bool low_pid = ((bdt_pi0_np > 0) && (bdt_pi0_np < 0.1)) || ((bdt_nonpi0_np > 0) && (bdt_nonpi0_np < 0.1));
    bool high_pid = ((bdt_pi0_np > 0.67) && (bdt_nonpi0_np > 0.70));
    bool high_energy = reco_e > 0.85;
    bool medium_energy = reco_e > 0.65;
    bool high_bdt = bdt_bkg_0p > 0.72;

    bool far_sideband = (low_pid || high_energy);
    bool signal_open = (high_pid && medium_energy);
    
    if (presel1eNp && signal_open) {

      std::cout << "Run, Event " << run << ", " << evt << " passes the 1eNp BDT selection for the (near+far) energy sideband in the BLIND file." << std::endl;

      far_sideband_BLIND += 1;
      
      if (BLIND_FAR_MAP.find(run) == BLIND_FAR_MAP.end()) {
	std::vector<int> evt_v = {evt};
	BLIND_FAR_MAP[run] = evt_v;
      }
      else {
	BLIND_FAR_MAP[run].push_back( evt );
      }
    }

  }// for all entries of BLIND tree


  // (1) are there the same number of entries in the far-sideband?

  std::cout << "Test (1): same number of events passing?" <<std::endl;

  if (far_sideband_BLIND != far_sideband_SIDEBAND) {
    std::cout << "FAIL -> did not find the sane number of far-sideband events. SIDEBAND file: " << far_sideband_SIDEBAND << ", and BLIND file: " << far_sideband_BLIND << std::endl;
    //exit(1);
  }
  else{
    std::cout << "PASS -> same number of events passing. SIDEBAND file: " << far_sideband_SIDEBAND << ", and BLIND file: " << far_sideband_BLIND << std::endl;
  }

  // (2) does every BLIND event have a match in the SIDEBAND file?

  std::cout << "Test (2): does every BLIND event have a match in the SIDEBAND file?" << std::endl;

  int nfailB = 0;
  
  for (auto itB = BLIND_FAR_MAP.begin(); itB != BLIND_FAR_MAP.end(); itB++) {

    int runBLIND = itB->first;
    std::vector<int> evtBLIND_v = itB->second;

    bool MATCHRUN = false;
    
    for (auto itS = SIDEBAND_FAR_MAP.begin(); itS != SIDEBAND_FAR_MAP.end(); itS++) {

      int runSIDEBAND = itS->first;
      std::vector<int> evtSIDEBAND_v = itS->second;

      if (runSIDEBAND != runBLIND) continue;

      // if made it this far the runs match, check event-by-event
      MATCHRUN = true;
      
      for (size_t iB=0; iB < evtBLIND_v.size(); iB++) {

	int evtBLIND = evtBLIND_v[iB];
	
	bool MATCHEVT = false;
	
	for (size_t iS=0; iS < evtSIDEBAND_v.size(); iS++) {

	  int evtSIDEBAND = evtSIDEBAND_v[iS];

	  if (evtSIDEBAND == evtBLIND){
	    MATCHEVT = true;
	    break;
	  }

	}// for all blind-file events matched to this run in the SIDEBAND file

	// if not matched this is an error!
	if (MATCHEVT == false) {
	  std::cout << "FAIL -> [run,event] [" << runBLIND << ", " << evtBLIND << "] not fund in SIDEBAND file." << std::endl;
	  nfailB += 1;
	}
	
      }// for all sideband-file events matched to this run in the BLIND file
      
    }// for all run vectors in SIDEBAND-file.

    if (MATCHRUN == false){
      std::cout << "FAIL -> run" << runBLIND << " not fund in BLIND file." << std::endl;
      nfailB += 1;
    }
    
  }// for all vectors in SIDEBAND-file.
  
  if (nfailB != 0){
    std::cout << "FAIL -> not all events that pass the far-sideband cuts match one-to-one." << std::endl;
  }
  else{
    std::cout << "PASS -> all events that pass the far-sideband cuts match one-to-one!" << std::endl;
  }


  // (3) flip the order: does every SIDEBAND event have a match in the BLIND file?
  int nfailS = 0;

  std::cout << "Test (3): does every SIDEBAND event have a match in the BLIND file?" <<std::endl;
  
  for (auto itS = SIDEBAND_FAR_MAP.begin(); itS != SIDEBAND_FAR_MAP.end(); itS++) {

    int runSIDEBAND = itS->first;
    std::vector<int> evtSIDEBAND_v = itS->second;

    bool MATCHRUN = false;
    
    for (auto itB = BLIND_FAR_MAP.begin(); itB != BLIND_FAR_MAP.end(); itB++) {

      int runBLIND = itB->first;
      std::vector<int> evtBLIND_v = itB->second;

      if (runSIDEBAND != runBLIND) continue;

      // if made it this far the runs match, check event-by-event
      MATCHRUN = true;
      
      for (size_t iS=0; iS < evtSIDEBAND_v.size(); iS++) {

	int evtSIDEBAND = evtSIDEBAND_v[iS];
	
	bool MATCHEVT = false;
	
	for (size_t iB=0; iB < evtBLIND_v.size(); iB++) {

	  int evtBLIND = evtBLIND_v[iB];

	  if (evtBLIND == evtSIDEBAND){
	    MATCHEVT = true;
	    break;
	  }

	}// for all blind-file events matched to this run in the BLIND file

	// if not matched this is an error!
	if (MATCHEVT == false) {
	  std::cout << "FAIL -> [run,event] [" << runSIDEBAND << ", " << evtSIDEBAND << "] not fund in BLIND file." << std::endl;
	  nfailS += 1;
	}
	
      }// for all sideband-file events matched to this run in the SIDEBAND file
      
    }// for all run vectors in BLIND-file.

    if (MATCHRUN == false){
      std::cout << "FAIL -> run" << runSIDEBAND << " not fund in BLIND file." << std::endl;
      nfailS += 1;
    }
    
  }// for all vectors in SIDEBAND-file.
  
  if (nfailS != 0){
    std::cout << "FAIL -> not all events that pass the far-sideband cuts match one-to-one." << std::endl;
    //exit(1);
  }
  else{
    std::cout << "PASS -> all events that pass the far-sideband cuts match one-to-one!" << std::endl;
  }

  if ( (nfailB==0) && (nfailS==0) && (far_sideband_BLIND == far_sideband_SIDEBAND)) {
    std::cout << "SUMMARY: TEST PASSED!" << std::endl;
  }
  else{
    std::cout << "SUMMARY: TEST FAILED..." << std::endl;
  }

}
