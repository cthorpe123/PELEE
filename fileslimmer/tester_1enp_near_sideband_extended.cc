#include "Riostream.h"
// #include "TString.h"
// #include "TFile.h"
// #include "TTree.h"
#include <map>
#include <iostream>
#include <cstdlib>

void tester_1enp_near_sideband_extended(TString finname)
{
  // Get old file, old tree and set top branch address
  TFile oldfile(finname);
  TTree *oldtree;
  oldfile.GetObject("nuselection/NeutrinoSelectionFilter", oldtree);

  int numevts = 0;

  const auto nentries = oldtree->GetEntries();

  std::cout << "input file entries " << nentries << std::endl;

  // Deactivate all branches
  oldtree->SetBranchStatus("*", 1);

  int backtracked_pdg;

  int nslice;
  int selected;
  float shr_energy_tot_cali;
  float _opfilter_pe_beam;
  float _opfilter_pe_veto;
  int bnbdata;
  int extdata;
  uint n_tracks_contained;
  uint n_showers_contained;
  float bdt_pi0_np;
  float bdt_nonpi0_np;
  float reco_e;
  int n_showers;
  float contained_fraction;

  oldtree->SetBranchAddress("nslice", &nslice);
  oldtree->SetBranchAddress("selected", &selected);
  oldtree->SetBranchAddress("shr_energy_tot_cali", &shr_energy_tot_cali);
  oldtree->SetBranchAddress("n_tracks_contained", &n_tracks_contained);
  oldtree->SetBranchAddress("n_showers_contained", &n_showers_contained);
  oldtree->SetBranchAddress("bdt_pi0_np", &bdt_pi0_np);
  oldtree->SetBranchAddress("bdt_nonpi0_np", &bdt_nonpi0_np);
  oldtree->SetBranchAddress("reco_e", &reco_e);
  oldtree->SetBranchAddress("n_showers", &n_showers);
  oldtree->SetBranchAddress("contained_fraction", &contained_fraction);

  std::cout << "Start loop with entries " << nentries << std::endl;

  for (auto i : ROOT::TSeqI(nentries))
  {
    if (i % 10000 == 0)
    {
      std::cout << "Entry num  " << i << std::endl;
    }

    oldtree->GetEntry(i);

    bool preseq = (nslice == 1) &&
      //(selected == 1) &&
      ( (contained_fraction > 0.4) && (n_showers_contained > 0) ) &&
      (shr_energy_tot_cali > 0.07);

    /*
    if (preseq)
      std::cout << "preseq++" << std::endl;
    else
      continue;
    */

    bool np_preseq = preseq && (n_tracks_contained > 0);

    /*
    if (np_preseq)
      std::cout << "np_preseq++" << std::endl;
    else
      continue;
    */

    bool np_preseq_one_shower = np_preseq && (n_showers_contained == 1);

    /*
    if (np_preseq_one_shower)
      std::cout << "np_preseq_one_shower++" << std::endl;
    else
      continue;
    */

    bool low_pid = ((bdt_pi0_np > 0) && (bdt_pi0_np < 0.67)) || ((bdt_nonpi0_np > 0) && (bdt_nonpi0_np < 0.7));

    /*
    if (low_pid)
      std::cout << "low_pid++" << std::endl;
    */

    bool high_energy = (reco_e > 0.65);

    /*
    if (high_energy)
      std::cout << "high_energy++" << std::endl;
    */

    bool near_sideband = (low_pid || high_energy);

    /*
    if (near_sideband)
      std::cout << "near_sideband++" << std::endl;
    */

    if (np_preseq_one_shower && !near_sideband)
    {
      std::cout << "you can't end up here! test failed." << std::endl;
      std::cout << "at entry i=" << i << " reco_e=" << reco_e << " bdt_pi0_np=" << bdt_pi0_np << " bdt_nonpi0_np=" << bdt_nonpi0_np << std::endl;
      exit(1);
    }// if cuts pass
  }// for all entries
  std::cout << "test passed!" << std::endl;
}
