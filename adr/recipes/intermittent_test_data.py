from __future__ import print_function, absolute_import

import json
from collections import defaultdict

from ..cli import RecipeParser
from ..query import format_date, run_query


def run(args):
    parser = RecipeParser('date')
    parser.add_argument('-b', '--branch', default=['mozilla-inbound'],
                        help="Branches to query results from.")
    parser.add_argument('-c', '--build_type', default='opt',
                        help="build configuration, default is 'opt'.")
    parser.add_argument('-p', '--platform', default='windows10-64',
                        help="build configuration, default is 'windows10-64'.")
    parser.add_argument('-t', '--test', default='',
                        help="Filter on specific test name")
    args = parser.parse_args(args)

    if args.test == '':
        args.test = '(~(file.*|http.*))'
        args.platform_config = "test-%s/%s" % (args.platform, args.build_type)
        args.groupby = 'result.test'
        args.result = ["F"]
    else:
        args.test = '.*%s.*' % args.test
        args.platform_config = "test-"
        args.groupby = 'run.key'
        args.result = ["T", "F"]

    result = []
    query_args = vars(args)

    result = next(run_query('intermittent_tests', **query_args))['data']
    total_runs = next(run_query('intermittent_test_rate', **query_args))['data']

    intermittent_tests = []
    for item in result['run.key']:
        parts = item.split('/')
        config = "%s/%s" % (parts[0], parts[1].split('-')[0])
        if config not in intermittent_tests:
            intermittent_tests.append(config)

    retVal = {}
    for test in total_runs:
        parts = test[0].split('/')
        config = "%s/%s" % (parts[0], parts[1].split('-')[0])
        if config in intermittent_tests:
            if config not in retVal:
                retVal[config] = [test[1], test[2]]
            else:
                retVal[config][0] += test[1]
                retVal[config][1] += test[2]

    result = []
    for item in retVal:
        val = [item]
        val.extend(retVal[item])
        result.append(val)
    result.insert(0, ['Config', 'Failures', 'Runs'])
    return result