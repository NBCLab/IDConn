import numpy as np
import pandas as pd
from os import makedirs
from os.path import join, exists
from nilearn.input_data import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from nilearn.plotting import plot_anat, plot_roi
import bct
from nipype.interfaces.fsl import InvWarp, ApplyWarp
import datetime

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
    "213",
    "214",
    "215",
    "216",
    "217",
    "218",
    "219",
    "320",
    "321",
    "322",
    "323",
    "324",
    "325",
    "327",
    "328",
    "329",
    "330",
    "331",
    "332",
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
    "347",
    "348",
    "349",
    "350",
    "451",
    "452",
    "453",
    "455",
    "456",
    "457",
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
    "575",
    "577",
    "578",
    "579",
    "580",
    "581",
    "582",
    "584",
    "585",
    "586",
    "587",
    "588",
    "589",
    "590",
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
    "611",
    "612",
    "613",
    "614",
    "615",
    "616",
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
    "628",
    "629",
    "630",
    "631",
    "633",
    "634",
]
# subjects = ['101', '102']


data_dir = "/home/data/nbc/physics-learning/data/pre-processed/"
sink_dir = "/home/data/nbc/physics-learning/retrieval-graphtheory/output"

shen = "/home/kbott006/physics-retrieval/shen2015_2mm_268_parcellation.nii.gz"
craddock = "/home/kbott006/physics-retrieval/craddock2012_tcorr05_2level_270_2mm.nii.gz"
masks = {"shen2015": shen, "craddock2012": craddock}

sessions = [0, 1]
sesh = ["pre", "post"]
tasks = ["rest"]
condition = ["rest"]
kappa_upper = 0.21
kappa_lower = 0.31

lab_notebook_dir = "/home/kbott006/lab_notebook/"
index = pd.MultiIndex.from_product([subjects, sessions], names=["subject", "session"])
lab_notebook = pd.DataFrame(index=index, columns=["start", "end", "errors"])

correlation_measure = ConnectivityMeasure(kind="correlation")

invert = InvWarp()
warpspeed = ApplyWarp(interp="nn")

index = pd.MultiIndex.from_product(
    [subjects, sessions, tasks, condition, masks.keys()],
    names=["subject", "session", "task", "condition", "mask"],
)
df = pd.DataFrame(
    index=index, columns=["efficiency", "charpath", "modularity"], dtype=np.float64
)

for subject in subjects:
    for session in sessions:
        lab_notebook.at[(subject, session), "start"] = str(datetime.datetime.now())
        if not exists(
            join(
                sink_dir,
                sesh[session],
                subject,
                "{0}-session-{1}_rest_mni-fnirt-epi-warp.nii.gz".format(
                    subject, session
                ),
            )
        ):
            try:
                mni2epiwarp = join(
                    sink_dir,
                    sesh[session],
                    subject,
                    "{0}-session-{1}_rest_mni-fnirt-epi-warp.nii.gz".format(
                        subject, session
                    ),
                )

                # invert the epi-to-mni warpfield so you can run these analyses in native space
                invert.inputs.warp = join(
                    data_dir,
                    subject,
                    "session-{0}".format(session),
                    "resting-state/resting-state-0/endor1.feat/reg/example_func2standard_warp.nii.gz",
                )
                invert.inputs.inverse_warp = mni2epiwarp
                invert.inputs.reference = join(
                    data_dir,
                    subject,
                    "session-{0}".format(session),
                    "resting-state/resting-state-0/endor1.feat/reg/example_func.nii.gz",
                )
                inverted = invert.run()

                warpspeed.inputs.ref_file = join(
                    data_dir,
                    subject,
                    "session-{0}".format(session),
                    "resting-state/resting-state-0/endor1.feat/reg/example_func.nii.gz",
                )
                warpspeed.inputs.field_file = inverted.outputs.inverse_warp

                xfmd_masks = {}
                for mask in masks.keys():
                    mask_nativespace = join(
                        sink_dir,
                        sesh[session],
                        subject,
                        "{0}-session-{1}_rest_{2}.nii.gz".format(
                            subject, session, mask
                        ),
                    )
                    warpspeed.inputs.in_file = masks[mask]
                    warpspeed.inputs.out_file = mask_nativespace
                    warped = warpspeed.run()
                    xfmd_masks[mask] = mask_nativespace

                    display = plot_roi(
                        mask_nativespace,
                        bg_img=join(
                            data_dir,
                            subject,
                            "session-{0}".format(session),
                            "resting-state/resting-state-0/endor1.feat/reg/example_func.nii.gz",
                        ),
                        colorbar=True,
                    )
                    display.savefig(
                        join(
                            sink_dir,
                            "qa",
                            "{0}-session-{1}_rest_qa_{2}.png".format(
                                subject, session, mask
                            ),
                        ),
                        dpi=300,
                    )
                    display.close()
            except Exception as e:
                print(e)
        try:
            # shen_masker = NiftiLabelsMasker(xfmd_masks['shen2015'], background_label=0, standardize=True, detrend=True,t_r=3.)
            # craddock_masker = NiftiLabelsMasker(xfmd_masks['craddock2012'], background_label=0, standardize=True, detrend=True,t_r=3.)

            # confounds = '/home/data/nbc/physics-learning/anxiety-physics/output/{1}/{0}/{0}_confounds.txt'.format(subject, sesh[session])
            # epi_data = join(data_dir, subject, 'session-{0}'.format(session), 'resting-state/resting-state-0/endor1.feat', 'filtered_func_data.nii.gz')

            # shen_ts = shen_masker.fit_transform(epi_data, confounds)
            # shen_corrmat = correlation_measure.fit_transform([shen_ts])[0]
            # np.savetxt(join(sink_dir, sesh[session], subject, '{0}-session-{1}-rest_network_corrmat_shen2015.csv'.format(subject, session)), shen_corrmat, delimiter=",")
            shen_corrmat = np.genfromtxt(
                join(
                    sink_dir,
                    sesh[session],
                    subject,
                    "{0}-session-{1}-rest_network_corrmat_shen2015.csv".format(
                        subject, session
                    ),
                ),
                delimiter=",",
            )

            # craddock_ts = craddock_masker.fit_transform(epi_data, confounds)
            # craddock_corrmat = correlation_measure.fit_transform([craddock_ts])[0]
            # np.savetxt(join(sink_dir, sesh[session], subject, '{0}-session-{1}-rest_network_corrmat_craddock2012.csv'.format(subject, session)), craddock_corrmat, delimiter=",")
            craddock_corrmat = np.genfromtxt(
                join(
                    sink_dir,
                    sesh[session],
                    subject,
                    "{0}-session-{1}-rest_network_corrmat_craddock2012.csv".format(
                        subject, session
                    ),
                ),
                delimiter=",",
            )

            ge_s = []
            ge_c = []
            cp_s = []
            cp_c = []
            md_s = []
            md_c = []
            for p in np.arange(kappa_upper, kappa_lower, 0.01):
                ntwk = []
                shen_thresh = bct.threshold_proportional(shen_corrmat, p, copy=True)
                craddock_thresh = bct.threshold_proportional(
                    craddock_corrmat, p, copy=True
                )
                # network measures of interest here
                # global efficiency
                ge = bct.efficiency_wei(shen_thresh)
                ge_s.append(ge)
                ge = bct.efficiency_wei(craddock_thresh)
                ge_c.append(ge)

                # characteristic path length
                dist = bct.distance_wei(shen_thresh)
                cp = bct.charpath(dist)
                cp_s.append(cp[0])
                dist = bct.distance_wei(craddock_thresh)
                cp = bct.charpath(dist)
                cp_c.append(cp[0])

                # modularity
                md = bct.modularity_louvain_und(shen_thresh)
                md_s.append(md[1])
                md = bct.modularity_louvain_und(craddock_thresh)
                md_c.append(md[1])
            df.at[
                (subject, session, "rest", "rest", "shen2015"), "efficiency"
            ] = np.trapz(ge_s, dx=0.1)
            df.at[
                (subject, session, "rest", "rest", "shen2015"), "charpath"
            ] = np.trapz(cp_s, dx=0.1)
            df.at[
                (subject, session, "rest", "rest", "shen2015"), "modularity"
            ] = np.trapz(md_s, dx=0.1)
            df.at[
                (subject, session, "rest", "rest", "craddock2012"), "efficiency"
            ] = np.trapz(ge_c, dx=0.1)
            df.at[
                (subject, session, "rest", "rest", "craddock2012"), "charpath"
            ] = np.trapz(cp_c, dx=0.1)
            df.at[
                (subject, session, "rest", "rest", "craddock2012"), "modularity"
            ] = np.trapz(md_c, dx=0.1)
            # df.to_csv(join(sink_dir, 'resting-state_graphtheory_shen+craddock.csv'), sep=',')
            lab_notebook.at[(subject, session), "end"] = str(datetime.datetime.now())
        except Exception as e:
            print(e, subject, session)
            lab_notebook.at[(subject, session), "errors"] = [
                e,
                str(datetime.datetime.now()),
            ]
        df.to_csv(
            join(sink_dir, "resting-state_graphtheory_shen+craddock.csv"), sep=","
        )

df.to_csv(
    join(
        sink_dir,
        "resting-state_graphtheory_shen+craddock_{0}.csv".format(
            str(datetime.datetime.today())
        ),
    ),
    sep=",",
)
lab_notebook.to_csv(
    join(
        lab_notebook_dir,
        "resting-state-graph-theory_{0}.csv".format(str(datetime.datetime.now())),
    )
)
