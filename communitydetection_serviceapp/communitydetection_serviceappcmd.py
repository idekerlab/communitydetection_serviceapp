#!/usr/bin/env python
import os.path
import shutil
import sys
import argparse
import json

from cellmaps_generate_hierarchy.maturehierarchy import HiDeFHierarchyRefiner
from ndex2.cx2 import CX2Network
import tempfile
from cellmaps_generate_hierarchy.hierarchy import CDAPSHiDeFHierarchyGenerator


def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)
    parser.add_argument('input',
                        help='Input. Network in CX2 format.')
    parser.add_argument('--interactome_uuid', default=None,
                        help='Network UUID.')
    parser.add_argument('--tempdir', default='/tmp',
                        help='Directory needed to hold files temporarily for processing')
    parser.add_argument('--k', default=10,
                        help='HiDeF stability parameter')
    parser.add_argument('--algorithm', default='leiden',
                        help='HiDeF clustering algorithm parameter')
    parser.add_argument('--maxres', default=80,
                        help='HiDeF max resolution parameter')
    parser.add_argument('--containment_threshold', default=0.75,
                        help='Containment index threshold for pruning hierarchy')
    parser.add_argument('--jaccard_threshold', default=0.9,
                        help='Jaccard index threshold for merging similar clusters')
    parser.add_argument('--min_diff', default=1,
                        help='Minimum difference in number of proteins for every '
                             'parent-child pair')
    parser.add_argument('--min_system_size', default=4,
                        help='Minimum number of proteins each system must have to be kept')
    return parser.parse_args(args)


def get_edgelist_file(network, outdir):
    dest_path = os.path.join(outdir, "edgelist.tsv")
    with open(dest_path, 'w') as f:
        for edge_id, edge_obj in network.get_edges().items():
            s, t = edge_obj['s'], edge_obj['t']
            f.write(str(s) + '\t' + str(t) + '\n')
    return dest_path


def run_community_detection(outdir, parent_net_path, algorithm, maxres, k, containment_threshold,
                            jaccard_threshold, min_system_size, min_diff, interactome_uuid):
    parent_network = CX2Network()
    parent_network.create_from_raw_cx2(parent_net_path)
    edgelist_file = get_edgelist_file(parent_network, outdir)
    refiner = HiDeFHierarchyRefiner(ci_thre=containment_threshold,
                                    ji_thre=jaccard_threshold,
                                    min_term_size=min_system_size,
                                    min_diff=min_diff,
                                    provenance_utils=None)

    generator = CDAPSHiDeFHierarchyGenerator(refiner=refiner)
    hierarchy, _ = generator.get_hierarchy_from_edgelists(outdir, [edgelist_file],
                                                          parent_network, algorithm, maxres, k)
    hierarchy.add_network_attribute('name', "Hierarchy generated by community detection service app")
    if interactome_uuid is not None:
        hierarchy.add_network_attribute('HCX::interactionNetworkUUID', str(interactome_uuid))
        if 'HCX::interactionNetworkName' in hierarchy.get_network_attributes():
            hierarchy.remove_network_attribute('HCX::interactionNetworkName')
    return [hierarchy.to_cx2()]


def main(args):
    """
    Main entry point for program

    :param args: command line arguments usually :py:const:`sys.argv`
    :return: 0 for success otherwise failure
    :rtype: int
    """
    desc = """
    TODO add weight column and list of cut offs and generate multiple interactomes
    """

    theargs = _parse_arguments(desc, args[1:])
    try:
        temp_outdir = tempfile.mkdtemp(dir=theargs.tempdir)
        try:
            theres = run_community_detection(temp_outdir, theargs.input, theargs.algorithm, theargs.maxres,
                                             theargs.k, theargs.containment_threshold, theargs.jaccard_threshold,
                                             theargs.min_system_size, theargs.min_diff, theargs.interactome_uuid)
        finally:
            shutil.rmtree(temp_outdir)

        if theres is None:
            sys.stderr.write('No results\n')
        else:
            json.dump(theres, sys.stdout, indent=2)
        sys.stdout.flush()
        return 0
    except Exception as e:
        sys.stderr.write('Caught exception: ' + str(e))
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
