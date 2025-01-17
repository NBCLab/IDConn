from __future__ import division
from os.path import join, basename, exists
from os import makedirs
from glob import glob

from nilearn import input_data, datasets, plotting
from nilearn.image import concat_imgs
from nilearn.input_data import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from scipy.stats import pearsonr

import bct
import json
import numpy as np
import pandas as pd

labels = [
    "limbic",
    "limbic",
    "orbitofrontal",
    "orbitofrontal",
    "basal ganglia",
    "salience",
    "salience",
    "salience",
    "hunger",
    "hunger",
    "hunger",
    "hunger",
    "hunger",
    "hunger",
    "hunger",
    "motor learning",
    "frontoparietal",
    "frontoparietal",
    "frontoparietal",
    "hand",
    "hand",
    "hand",
    "motor execution",
    "motor execution",
    "higher order visual",
    "higher order visual",
    "lateral visual",
    "lateral visual",
    "medial visual",
    "default mode",
    "default mode",
    "default mode",
    "default mode",
    "default mode",
    " cerebellum",
    "right central executive",
    "right central executive",
    "right central executive",
    "right central executive",
    "right central executive",
    "auditory",
    "auditory",
    "mouth",
    "mouth",
    "left central executive",
    "left central executive",
    "left central executive",
]


# only want post subjects
subjects = [
    "101",
    "102",
    "103",
    "104",
    "106",
    "107",
    "108",
    "110",
    "212",
    "214",
    "215",
    "216",
    "217",
    "218",
    "219",
    "320",
    "323",
    "324",
    "325",
    "327",
    "328",
    "330",
    "331",
    "333",
    "334",
    "335",
    "336",
    "337",
    "338",
    "339",
    "340",
    "341",
    "342",
    "343",
    "344",
    "345",
    "346",
    "348",
    "349",
    "350",
    "451",
    "453",
    "455",
    "458",
    "459",
    "460",
    "462",
    "463",
    "464",
    "465",
    "467",
    "468",
    "469",
    "470",
    "502",
    "503",
    "571",
    "572",
    "573",
    "574",
    "577",
    "578",
    "581",
    "582",
    "584",
    "585",
    "586",
    "587",
    "588",
    "589",
    "591",
    "592",
    "593",
    "594",
    "595",
    "596",
    "597",
    "598",
    "604",
    "605",
    "606",
    "607",
    "608",
    "609",
    "610",
    "612",
    "613",
    "614",
    "615",
    "617",
    "618",
    "619",
    "620",
    "621",
    "622",
    "623",
    "624",
    "625",
    "626",
    "627",
    "629",
    "630",
    "631",
    "633",
    "634",
]
# subjects = ['633', '634']
# all subjects 102 103 101 104 106 107 108 110 212 X213 214 215 216 217 218 219 320 321 X322 323 324 325
# 327 328 X329 330 331 X332 333 334 335 336 337 338 339 340 341 342 343 344 345 346 347 348 349 350 451
# X452 453 455 X456 X457 458 459 460 462 463 464 465 467 468 469 470 502 503 571 572 573 574 X575 577 578
# X579 X580 581 582 584 585 586 587 588 589 X590 591 592 593 594 595 596 597 598 604 605 606 607 608 609
# 610 X611 612 613 614 615 X616 617 618 619 620 621 622 623 624 625 626 627 X628 629 630 631 633 634
# errors in fnirt-to-mni: 213, 322, 329, 332, 452, 456, 457, 575, 579, 580, 590, 611, 616, 628
# subjects without post-IQ measure: 452, 461, 501, 575, 576, 579, 583, 611, 616, 628, 105, 109, 211, 213, 322, 326, 329, 332
# subjects = ['101','103']
# something weird going on with the regionwise parcellation
# in subjects 321, 347 (run 0 has only 46 regions), 618 (run 1 only has 46 regions),
# 631 (run 1 has only 43 regions),
subjects = ["321", "347"]

# In[5]:


# data_dir = '/home/data/nbc/physics-learning/data/pre-processed'
data_dir = "/home/data/nbc/physics-learning/retrieval-graphtheory/output"
sink_dir = "/home/kbott006/physics-retrieval/output"

runs = [0, 1]
connectivity_metric = "correlation"
conditions = ["phy", "gen"]
thresh_range = np.arange(0.1, 1, 0.1)
highpass = 1 / 55.0

correlation_measure = ConnectivityMeasure(kind=connectivity_metric)


# In[ ]:


# gen_timing = np.genfromtxt('/home/data/nbc/physics-learning/physics-learning/RETRconditionGeneralSess1.txt',
#                           delimiter='\t')
gen_timing = np.genfromtxt(
    "/home/data/nbc/physics-learning/retrieval-graphtheory/RETRconditionGeneralSess1.txt",
    delimiter="\t",
    dtype=int,
)

gen_timing = (gen_timing / 2) - 1
gen_timing = gen_timing[:, 0:2]

# phy_timing = np.genfromtxt('/home/data/nbc/physics-learning/physics-learning/RETRconditionPhysicsSess1.txt',
#                           delimiter='\t')
phy_timing = np.genfromtxt(
    "/home/data/nbc/physics-learning/retrieval-graphtheory/RETRconditionPhysicsSess1.txt",
    delimiter="\t",
)
phy_timing = (phy_timing / 2) - 1
phy_timing = phy_timing[:, 0:2]
timing = {}
timing["phy"] = phy_timing
timing["gen"] = gen_timing


# run preprocessing once per run per subject
for subject in subjects:
    try:
        print subject
        ntwk_run_cond = {}
        ntwk = {}
        hipp = {}
        hipp_run_cond = {}
        corrmats = {}
        for run in runs:
            # xfm laird 2011 maps to subject's epi space & define masker
            epi = join(
                data_dir, subject, "{0}-{1}_retr-mcf.nii.gz".format(subject, run)
            )
            confounds = join(
                data_dir, subject, "{0}-{1}_retr-confounds.txt".format(subject, run)
            )
            # icn = join(data_dir, subject,'{0}-{1}_18_icn_retr.nii.gz'.format(subject, run))
            # icn_regions = connected_label_regions(icn, min_size=50., labels=labels)
            icn_regions = join(
                data_dir,
                subject,
                "{0}-{1}_18_icn-regions_retr.nii.gz".format(subject, run),
            )
            hippo = join(
                data_dir, subject, "{0}-{1}_hippo_retr.nii.gz".format(subject, run)
            )
            regn_masker = NiftiLabelsMasker(
                icn_regions, standardize=True, high_pass=highpass, t_r=2.0, verbose=1
            )
            hipp_masker = NiftiLabelsMasker(
                hippo, standardize=True, high_pass=highpass, t_r=2.0, verbose=1
            )

            # extract the network-wise and hippocampus timeseries per run
            # fmri = join(data_dir, subject, 'session-1', 'retr', 'mni', '{0}_filtered_func_data_{1}.nii.gz'.format(subject, run))
            ntwk_ts = regn_masker.fit_transform(epi, confounds=confounds)
            hipp_ts = hipp_masker.fit_transform(epi, confounds=confounds)
            # ts = [ntwk_ts, hipp_ts]
            # and then separate each run's timeseries into the different conditions
            for condition in conditions:
                ntwk_run_cond["{0} {1}".format(condition, run)] = np.vstack(
                    (
                        ntwk_ts[
                            timing[condition][0, 0]
                            .astype(int) : (
                                timing[condition][0, 0] + timing[condition][0, 1] + 1
                            )
                            .astype(int),
                            :,
                        ],
                        ntwk_ts[
                            timing[condition][1, 0]
                            .astype(int) : (
                                timing[condition][1, 0] + timing[condition][1, 1] + 1
                            )
                            .astype(int),
                            :,
                        ],
                        ntwk_ts[
                            timing[condition][2, 0]
                            .astype(int) : (
                                timing[condition][2, 0] + timing[condition][2, 1] + 1
                            )
                            .astype(int),
                            :,
                        ],
                    )
                )
                print ntwk_run_cond["{0} {1}".format(condition, run)].shape
                hipp_run_cond["{0} {1}".format(condition, run)] = np.vstack(
                    (
                        hipp_ts[
                            timing[condition][0, 0]
                            .astype(int) : (
                                timing[condition][0, 0] + timing[condition][0, 1] + 1
                            )
                            .astype(int)
                        ],
                        hipp_ts[
                            timing[condition][1, 0]
                            .astype(int) : (
                                timing[condition][1, 0] + timing[condition][1, 1] + 1
                            )
                            .astype(int)
                        ],
                        hipp_ts[
                            timing[condition][2, 0]
                            .astype(int) : (
                                timing[condition][2, 0] + timing[condition][2, 1] + 1
                            )
                            .astype(int)
                        ],
                    )
                )
        for condition in conditions:
            ntwk[condition] = np.vstack(
                (
                    ntwk_run_cond["{0} 0".format(condition)],
                    ntwk_run_cond["{0} 1".format(condition)],
                )
            )
            hipp[condition] = np.vstack(
                (
                    hipp_run_cond["{0} 0".format(condition)],
                    hipp_run_cond["{0} 1".format(condition)],
                )
            )
            corrmats[condition] = correlation_measure.fit_transform([ntwk[condition]])[
                0
            ]
            df = pd.DataFrame(corrmats[condition], index=labels, columns=labels)
            df.to_csv(
                join(
                    sink_dir,
                    "{0}-{1}-corrmat-regionwise.csv".format(subject, condition),
                )
            )
            df.to_csv(
                join(
                    data_dir,
                    subject,
                    "{0}-{1}-corrmat-regionwise.csv".format(subject, condition),
                )
            )
    except Exception as e:
        print e
