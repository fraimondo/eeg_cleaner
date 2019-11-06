import mne
import numpy as np

import mne
from mne.utils import logger
import matplotlib.pyplot as plt


def create_ica_report(ica, epochs, filename, ncomponents=None):

    try:
        import nice_ext
        layout, outlines = nice_ext.equipments.prepare_layout(
            epochs.info['description'], epochs.info)
    except ImportError:
        layout = mne.channels.make_eeg_layout(epochs.info)
        outlines = 'head'

    topomap_args = {'outlines': outlines, 'layout': layout}

    json_fname = filename.replace('.fif', '.json')

    if ncomponents is None or ncomponents == -1:
        ncomponents = ica.n_components_
    else:
        ncomponents = min(ncomponents, ica.n_components_)

    report = mne.Report(title='ICA Components')

    style = u"""
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
        });

        function ica_summarize() {
            var to_reject = $('input[value="reject"]:checked').map(
                function(o, i) {return parseInt(i.name.replace('ica_', ''));});
            var to_render = '<h3> Components to reject</h3><br />'
            for (var ica_comp = 0; ica_comp < to_reject.length; ica_comp ++) {
                if (ica_comp > 0) {
                    to_render += ' - ';
                }
                to_render +=  to_reject[ica_comp];
            }
            $('#ica_selected').html(to_render);
        }

        function ica_json() {
            var to_reject = $('input[value="reject"]:checked').map(
                function(o, i) {return parseInt(i.name.replace('ica_', ''));});
            var txtFile = $('#json_fname').val();
            var data = {reject: to_reject.get()}
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

    report.include += style
    fig_comps = ica.plot_components(inst=epochs, outlines=outlines,
                                    layout=layout, picks=range(ncomponents))

    overall_comment = u"""
    <div class="ica_menu">
        <input id="ica_check" type="button" value="Summarize"
        onclick="ica_summarize();" />
        <div id="ica_selected"></div>
        <input id="ica_save" type="button" value="Save to JSON"
        onclick="ica_json();" />
        <input type="hidden" id="json_fname" value="{0}">

    </div>"""

    report.add_figs_to_section(figs=[fig_comps], captions=['Topographies'],
                               section='Overall',
                               comments=[overall_comment.format(json_fname)])
    plt.close(fig_comps)

    figs_props = ica.plot_properties(epochs, picks=range(ncomponents),
                                          topomap_args=topomap_args)
    figs_ts = []
    sources = ica.get_sources(epochs).get_data()
    n_sources = sources.shape[0]
    n_random = 5
    n_epochs = 5
    for i_comp in range(ncomponents):
        logger.info('Plotting component {} of {}'.format(
            i_comp + 1, ncomponents))
        idx = np.random.randint(n_sources - n_epochs, size=n_random)
        fig, axes = plt.subplots(n_random, 1, figsize=(7, 4))
        for i, ax in zip(idx, axes):
            data = sources[i:i+n_epochs, i_comp, :]
            ax.plot(np.hstack(data), lw=0.5, color='k')
            [ax.axvline(data.shape[1] * x, ls='--', lw=0.2, color='k')
             for x in range(n_epochs)]
        figs_ts.append(fig)

    eptype = list(epochs.event_id.keys())[0].split('/')[-1]
    props_captions = ['{} - {}'.format(eptype, x) for x in range(ncomponents)]

    captions = [elt for sublist in zip(props_captions, props_captions)
                for elt in sublist]

    ts_comments = [''] * len(figs_ts)

    prop_comment = u"""
    <form action="" class="ica_select">
        <input type="radio" name="ica_{0}" value="accept" checked>Accept
        <input type="radio" name="ica_{0}" value="reject">Reject
    </form>"""
    comments = [prop_comment.format(x) for x in range(ncomponents)]
    comments = [elt for sublist in zip(comments, ts_comments)
                for elt in sublist]

    figs = [elt for sublist in zip(figs_props, figs_ts)
            for elt in sublist]
    report.add_figs_to_section(figs=figs, captions=captions,
                               comments=comments, section='Details')
    [plt.close(x) for x in figs_props]

    return report