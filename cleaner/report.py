# NICE-EEG Cleaner
# Copyright (C) 2019 - Authors of NICE-EEG-Cleaner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# You can be released from the requirements of the license by purchasing a
# commercial license. Buying such a license is mandatory as soon as you
# develop commercial activities as mentioned in the GNU Affero General Public
# License version 3 without disclosing the source code of your own
# applications.
#
import json

import matplotlib.pyplot as plt
import mne
import numpy as np
from mne.utils import logger
from mne.viz.ica import _create_properties_layout


def create_ica_report(ica, epochs, filename, ncomponents=None):
    outlines = "head"

    topomap_args = {"outlines": outlines}

    json_fname = filename.with_suffix(".json")

    if ncomponents is None or ncomponents == -1:
        ncomponents = ica.n_components_
    else:
        ncomponents = min(ncomponents, ica.n_components_)

    logger.info(f"Plotting {ncomponents} components")

    report = mne.Report(title="Cleaning report")

    style_start = """
    <style type="text/css">
        div.ica_menu,
        form.ica_select {
            text-align: center;
        }

        div#ica_selected {
            font-size: 20px;
            margin-bottom: 5px;
        }

        form.ica_select input {
            margin-left: 10px;
            margin-right: 10px;
        }
    </style>
    <script type="text/javascript">
        $('document').ready(function(){
            $('.report_Details').each(
                function() {
                    $(this).css('width', '50%').css('float', 'left').css('height', '800px');
                }
            )
    """
    to_exclude = [f"{x}" for x in ica.exclude]
    style_start += (
        f"window.sessionStorage.ica_to_reject = '{json.dumps(to_exclude)}';"
    )

    style_start += """
            ica_to_reject = JSON.parse(sessionStorage.ica_to_reject || '[]');
            $('#accordion-collapse-Properties-ICA_properties .carousel-item').each(
                function(index, value) {
                    checked_accept = ""
                    checked_reject = ""
                    if (ica_to_reject.includes(index.toString())) {
                        checked_accept = "";
                        checked_reject = "checked";
                    } else {
                        checked_accept = "checked";
                        checked_reject = "";
                    }
                    thtml= '<div class="ica_select">'+
                    '<input type="radio" class="btn-check ica-selector" name="radio_ica'+index +'" id="ica_'+index+'_accept" ica='+index+' value="accept" autocomplete="off" '+checked_accept+'>'+
                    '<label class="btn btn-outline-success" for="ica_'+index+'_accept">Accept</label>' +
                    '<input type="radio" class="btn-check ica-selector" name="radio_ica'+index +'" id="ica_'+index+'_reject" ica='+index+' value="reject" autocomplete="off" '+checked_reject+'>'+
                    '<label class="btn btn-outline-danger" for="ica_'+index+'_reject">Reject</label>' +
                    
                    '</div>'
                    
                    $(this).append(thtml);
                }
            )
            $('input[type=radio].ica-selector').change(function() {
                ica_to_reject = JSON.parse(sessionStorage.ica_to_reject || '[]');
                tval = this.value;
                tica = this.getAttribute('ica');
                console.log(tval);
                console.log(tica);
                if (tval == 'reject') {
                    ica_to_reject.push(tica);
                } else {
                    ica_to_reject = ica_to_reject.filter(
                        function(e) { return e != tica; });
                }
                console.log(ica_to_reject);
                sessionStorage.ica_to_reject = JSON.stringify(ica_to_reject);
                ica_summarize()
            });

            $( "#accordion-collapse-Properties-ICA_properties" ).on( "keypress", function(event) {
                if (event.originalEvent.key == "r") {
                    t_name = $("#accordion-collapse-Properties-ICA_properties div.carousel-item.active input")[0].name
                    $("input[type='radio'][name='"+t_name+"']").not(':checked').prop("checked", true).trigger("change");
                }
            } );
            ica_summarize();
        });


        function ica_summarize() {
            var to_render = '<h3> Components to reject</h3><br />'
            ica_to_reject = JSON.parse(sessionStorage.ica_to_reject || '[]');
            ica_to_reject.sort();
            for (var ica_comp = 0; ica_comp < ica_to_reject.length; ica_comp ++) {
                if (ica_comp > 0) {
                    to_render += ' - ';
                }
                to_render += ica_to_reject[ica_comp];
            }
            console.log(to_render);
            $('#ica_selected').html(to_render);
        }

        function ica_json() {

            var to_reject = JSON.parse(sessionStorage.ica_to_reject || '[]');
            to_reject.sort();
            var txtFile = $('#json_fname').val();
            var data = {reject: to_reject}
            var str = JSON.stringify(data);

            download(str, txtFile, 'text/plain');
        }

        function download(strData, strFileName, strMimeType) {
            var D = document,
                A = arguments,
                a = D.createElement("a"),
                d = A[0],
                n = A[1],
                t = A[2] || "text/plain";

            //build download link:
            a.href = "data:" + strMimeType + "charset=utf-8," + escape(strData);


            if (window.MSBlobBuilder) { // IE10
                var bb = new MSBlobBuilder();
                bb.append(strData);
                return navigator.msSaveBlob(bb, strFileName);
            } /* end if(window.MSBlobBuilder) */

            if ('download' in a) { //FF20, CH19
                a.setAttribute("download", n);
                a.innerHTML = "downloading...";
                D.body.appendChild(a);
                setTimeout(function() {
                    var e = D.createEvent("MouseEvents");
                    e.initMouseEvent("click", true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                    a.dispatchEvent(e);
                    D.body.removeChild(a);
                }, 66);
                return true;
            }; /* end if('download' in a) */


            //do iframe dataURL download: (older W3)
            var f = D.createElement("iframe");
            D.body.appendChild(f);
            f.src = "data:" + (A[2] ? A[2] : "application/octet-stream") + (window.btoa ? ";base64" : "") + "," + (window.btoa ? window.btoa : escape)(strData);
            setTimeout(function() {
                D.body.removeChild(f);
            }, 333);
            return true;
        }
    </script>"""

    report.include += style_start

    unique_events = np.unique(epochs.events[:, 2])
    t_event_id = {
        k: v for k, v in epochs.event_id.items() if v in unique_events
    }
    report.add_events(
        events=epochs.events,
        event_id=t_event_id,
        title='Events from "events"',
        sfreq=epochs.info["sfreq"],
    )

    report.add_epochs(
        epochs=epochs,
        title="Epochs",
    )

    report._add_ica_overlay(
        ica=ica,
        inst=epochs,
        image_format=report.image_format,
        section="ICA Overlay",
        replace=True,
        tags=["ica_overlay"],
    )

    fig_comps = ica.plot_components(
        inst=epochs,
        outlines=outlines,
        picks=range(ncomponents),
        show=False,
    )

    overall_comment = """
    <div class="ica_menu">
        <div id="ica_selected"></div>
        <input id="ica_save" type="button" class="btn btn-primary" value="Save to JSON"
        onclick="ica_json();" />
        <input type="hidden" id="json_fname" value="{0}">

    </div>"""

    report.add_figure(
        fig=fig_comps,
        title="ICA components",
        caption="Topographies",
        section="Overall",
    )
    report.add_html(
        html=overall_comment.format(json_fname.name),
        title="ICA components",
        section="Overall",
    )
    plt.close(fig_comps)

    all_figs = []
    captions = []
    sources = ica.get_sources(epochs).get_data()
    n_sources = sources.shape[0]
    n_random = 5
    n_epochs = 5
    for t_comp in range(ncomponents):
        logger.info(f"Plotting component {t_comp+1} of {ncomponents}")
        fig = plt.figure(layout="constrained", figsize=(14, 6))
        subfigs = fig.subfigures(1, 2, hspace=0.07)
        t_prop_fig, axes = _create_properties_layout(fig=subfigs[0])
        ica.plot_properties(
            inst=epochs,
            picks=t_comp,
            axes=axes,
            topomap_args=topomap_args,
            show=False,
        )
        idx = np.random.randint(n_sources - n_epochs, size=n_random)
        axes = subfigs[1].subplots(n_random, 1)
        for i, ax in zip(idx, axes):
            data = sources[i : i + n_epochs, t_comp, :]
            ax.plot(np.hstack(data), lw=0.5, color="k")
            [
                ax.axvline(data.shape[1] * x, ls="--", lw=0.2, color="k")
                for x in range(n_epochs)
            ]
            ax.set_xticks(
                ticks=[x * data.shape[1] for x in range(n_epochs)],
                labels=[x * epochs.times[-1] for x in range(n_epochs)],
            )
        ax.set_ylabel("Amplitude (uV)")
        ax.set_xlabel("Time (s)")
        all_figs.append(fig)
        captions.append(
            f"ICA component {t_comp+1} topographies and time series"
        )

    report.add_figure(
        fig=all_figs,
        caption=captions,
        section="Properties",
        title="ICA properties",
    )
    [plt.close(x) for x in all_figs]

    return report
