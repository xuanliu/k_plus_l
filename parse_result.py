#!/usr/bin/python
"""
This script is to parse the results generated by expr_run.sh, to create a csv
file in the format of:
   ,4    ,9  ,16 ,25 , 36, 49, 64, 81
0.4,33.33,0.0,0.0,0.0,2.38,0.17,0.64,0.37
0.6,33.33,0.0,0.0,2.33,1.9,0.43,0.64,0.28
0.8,33.33,0.0,0.0,2.33,1.9,0.43,0.74,0.28
0.9,33.33,0.0,0.0,2.0,1.9,0.09,0.64,0.28
0.95,33.33,0.0,0.0,0.0,1.43,0.77,0.74,0.19

To run this script, needs to specify the obj type and load type and result 
filename.

By Xuan Liu
Jan 5, 2014
"""
import numpy as np
import csv
from optparse import OptionParser
import sys

def get_res_lines(result_file):
    ''' read the result file and return only the body of the results '''
    fopen = open(result_file)
    lines = fopen.readlines()
    result_body = lines[4:]
    return result_body



def result_filter(result_body, obj_type, load_type):
    ''' filt out the results respected to the obj_type and load_type '''
    new_result = []
    for line in result_body:
        key = obj_type + '_' + load_type + '_'
        if key in line:
            new_result.append(line)
        else:
            pass
    return new_result




def get_key_info(line):
    """
    return information about nodes, load-level, seed and MPM value 
    from a single line

    each line is in format of:
    file: <filename> seed : topo dc_type bin obj_type optimal load_type ...
            load_level new_cap num_node num_dpair mpmc mpm dualitygap
    """
    line_split = line.split(':')
    seed = line_split[1].split()[1]
    record = line_split[2].split()
    #print len(record)
    obj_index = record.index(record[3])
    
    if record[obj_index + 1] == 'bounds.' or record[obj_index + 2] == 'infeasible.':
        num_node = record[9]
        load_level = record[7]
        mpm_val = record[-2]
        obj_val = -1
    elif record[obj_index + 1] == 'infeasible.':
        #print record
        num_node = record[8]
        load_level = record[6]
        mpm_val = '-100.00'
        obj_val = -1
    elif record[-1] == '-100.00':
        #print record
        num_node = record[7]
        load_level = record[5]
        mpm_val = '-100.00'
        obj_val = -1
    elif '%' in record[obj_index + 1]:
        print "% appear"
        count = 0
        if "%" not in record[obj_index + 2]:
            print "ONE %"
            num_node = record[9]
            load_level = record[7]
            mpm_val = record[12]
        else:
            while "%" in record[obj_index + 2 + count]:
                count = count + 1
            print record
            print "More than one %", count
            num_node = record[9 + count]
            load_level = record[7 + count]
            mpm_val = record[12 + count]
            obj_val = record[obj_index + 1 + count]
        
    elif 'uniform' not in record[obj_index + 1]:
        #print record
        #print "REGULAR"
        num_node = record[8]
        load_level = record[6]
        mpm_val = record[11]
        obj_val = record[obj_index + 1]
        #print mpm_val
    else:
        print record
        num_node = record[7]
        load_level = record[5]
        mpm_val = record[-2]
        obj_val = -1
    #print "RECORD", record, '\n'
    #print record[obj_index + 1], num_node, record.index(num_node), '\n'

    #print "record", num_node, load_level, seed, mpm_val
    #line_dict = {}
    #if num_node == '64' and load_level == '0.9':
    #    print "CHECK", record, mpm_val
    return int(num_node), float(load_level), int(seed), float(mpm_val), float(obj_val)



def create_res_dict(filter_result):
    """
    create a dictionary for filtered result in the form of 
    {(num_node, load_level): {seed1: mpm1, seed2: mpm2, ...}}
    """
    res_dict = {}
    obj_dict = {}
    for item in filter_result:
        num_node, load_level, seed, mpm_val, obj_val = get_key_info(item)
        if num_node == 9 and load_level == 0.95:
            print "GRAP", mpm_val
        if (load_level, num_node) not in res_dict:
            res_dict[(load_level, num_node)] = {}
            obj_dict[(load_level, num_node)] = {}
            res_dict[(load_level, num_node)][seed] = mpm_val
            obj_dict[(load_level, num_node)][seed] = obj_val
        else:
            res_dict[(load_level, num_node)][seed] = mpm_val
            obj_dict[(load_level, num_node)][seed] = obj_val
    return res_dict, obj_dict


def get_mean_mpms(res_dict):
    """
    This function is to get the mean mpm value for each (load_level, num_node) 
    pair, under five seed runs.
    return a list of three-item tuple (load_level, num_node, avg_mpm)
    """
    print res_dict
    mpm_tuple_list = []
    for item in res_dict:
        mpm_list = res_dict[item].values()
        mean_mpm = round(np.mean(mpm_list), 4)
        if item == (0.9, 64):
            print "mean_mpm", mean_mpm, mpm_list
        mpm_tuple_list.append((item[0], item[1], mean_mpm))
    return mpm_tuple_list

def get_mean_obj(obj_dict):
    """
    This function is to get the mean obj value for each (load_level, num_node) 
    pair, under five seed runs.
    return a list of three-item tuple (load_level, num_node, avg_mpm)
    """
    print obj_dict
    obj_tuple_list = []
    for item in obj_dict:
        obj_list = obj_dict[item].values()
        mean_obj = round(np.mean(obj_list), 4)
        obj_tuple_list.append((item[0], item[1], mean_obj))
    return obj_tuple_list

def get_lb_mpms_mean(res_dict):
    """
    Get the mean mpms for lb cases: 
    First, take the minimum mpms for all laods, 
    and then take average for all seeds
    """
    lb_dict = {}
    for item in res_dict:
        if item[1] not in lb_dict:
            lb_dict[item[1]] = {}
        for seed in res_dict[item]:
            if seed not in lb_dict[item[1]]:
                lb_dict[item[1]][seed] = {}
            lb_dict[item[1]][seed][item[0]] = res_dict[item][seed]
    #print lb_dict

    mpm_dict = {}
    for size in lb_dict:
        mpm_dict[size] = {}
        for seed in lb_dict[size]:
            min_mpm = min(lb_dict[size][seed].values())
            mpm_dict[size][seed] = min_mpm
    
    load_level = [0.4, 0.6, 0.8, 0.9, 0.95]
    lb_mpm_tuple_list = []
    for load in load_level:
        for size in mpm_dict:
            mpm_list = mpm_dict[size].values()
            mean_mpm = round(np.mean(mpm_list), 4)
            lb_mpm_tuple_list.append((load, size, mean_mpm))
    #print lb_mpm_tuple_list
    return lb_mpm_tuple_list
    #return lb_dict, mpm_dict, lb_mpm_tuple_list
            
def get_lb_obj_mean(obj_dict):
    """
    Get the mean objs for lb cases: 
    First, take the minimum objs for all laods, 
    and then take average for all seeds
    """
    lb_dict = {}
    for item in obj_dict:
        if item[1] not in lb_dict:
            lb_dict[item[1]] = {}
        for seed in obj_dict[item]:
            if seed not in lb_dict[item[1]]:
                lb_dict[item[1]][seed] = {}
            lb_dict[item[1]][seed][item[0]] = obj_dict[item][seed]
    #print lb_dict

    obj_dict = {}
    for size in lb_dict:
        obj_dict[size] = {}
        for seed in lb_dict[size]:
            min_obj = min(lb_dict[size][seed].values())
            obj_dict[size][seed] = min_obj
    
    load_level = [0.4, 0.6, 0.8, 0.9, 0.95]
    lb_obj_tuple_list = []
    for load in load_level:
        for size in obj_dict:
            obj_list = obj_dict[size].values()
            mean_obj = round(np.mean(obj_list), 4)
            lb_obj_tuple_list.append((load, size, mean_obj))
    #print lb_mpm_tuple_list
    return lb_obj_tuple_list
    #return lb_dict, mpm_dict, lb_mpm_tuple_list   

def create_csv(mpm_tuple_list, csv_filename='test.csv'):
    """
    create a csv file that has following format:
    
    num_nodes      4   9   16   25    36    49    64
    load_level    mpm mpm  mpm  mpm   mpm   mpm   mpm
    0.4
    0.6
    0.8
    0.9
    0.95

    The mpm_tuple_list is in format of 
    [(0.4, 4, 33.33),
     (0.4, 9, 0.0),
     (0.4, 16, 0.0),
     (0.4, 25, 0.0),
     (0.4, 36, 2.38),
     (0.4, 49, 0.17),
     (0.4, 64, 0.64),
     (0.4, 81, 0.37),
     (0.6, 4, 33.33),
     (0.6, 9, 0.0),
     (0.6, 16, 0.0),
     (0.6, 25, 2.33),
     (0.6, 36, 1.9),
     (0.6, 49, 0.43),
     (0.6, 64, 0.64),
     (0.6, 81, 0.28),...]

    """
    
       
    node_varies = len(mpm_tuple_list)/5
    max_node = mpm_tuple_list[node_varies - 1][1]
    min_node = mpm_tuple_list[0][1]
    mpm_matrix = []
    heading = [' ']
    for num_node in range(node_varies):
        heading.append(mpm_tuple_list[num_node][1])
    #print heading
    mpm_matrix.append(heading)
    for item in mpm_tuple_list:
        if item[1] == min_node:
            sub_list = []
            sub_list.append(item[0])
            sub_list.append(item[2])
        else:
            sub_list.append(item[2])
        if item[1] == max_node:
            mpm_matrix.append(sub_list)
        else:
            pass

    csv_writer = csv.writer(open(csv_filename, 'w'), delimiter=',')
       
    #print mpm_matrix
    for row in mpm_matrix:
        csv_writer.writerow(row)

def create_option(parser):
    """
    add the options to the parser:
    takes arguments from commandline
    """
    parser.add_option("-v", action="store_true",
                      dest="verbose",
                      help="Print output to screen")
    parser.add_option("-w", dest="csv_file",
                      type="str",
                      default="sample.csv",
                      help="Create csv file for mpm information")
    parser.add_option("-W", dest="obj_csv",
                      type="str",
                      default="obj.csv",
                      help="create csv file for obj information")
    parser.add_option("-r", dest="result_file",
                      type="str",
                      default="sample_result.txt",
                      help="read the result file")
    parser.add_option("--obj", dest="obj_type",
                      type="str",
                      default="lb",
                      help="objective type: mcr/lb/ad")
    parser.add_option("--load", dest="load_type",
                      type="str",
                      default="uniform",
                      help="""
                           traffic load type: uniform, uniforme1n, uniformeij,
                           nonuniform, nonuniformh, nonuniforme1n, nonuniformeij
                           """)

def run(argv=None):
    ''' program wrapper '''
    """
    program wrapper
    """
    if not argv:
        argv=sys.argv[1:]
    usage = ("""%prog [-v verbose] 
                    [-w csv_file] 
                    [-W obj_csv]
                    [-r result_file]
                    [--obj obj_type
                    [--load] load_type]""")
    parser = OptionParser(usage=usage)
    create_option(parser)
    (options, _) = parser.parse_args(argv)
    
    # take arguments
    csv_file = options.csv_file
    result_file = options.result_file
    obj_type = options.obj_type
    load_type = options.load_type
    obj_csv = options.obj_csv


    result_body = get_res_lines(result_file)
    filtered_res = result_filter(result_body, obj_type, load_type)
    res_dict, obj_dict = create_res_dict(filtered_res)
    if obj_type == 'lb':
        mpm_tuple_list = get_lb_mpms_mean(res_dict)
        
    else:
        mpm_tuple_list = get_mean_mpms(res_dict)
        
    obj_tuple_list = get_mean_obj(obj_dict)
    mpm_tuple_list.sort()
    obj_tuple_list.sort()
    print mpm_tuple_list, obj_tuple_list
    create_csv(mpm_tuple_list, csv_file)
    create_csv(obj_tuple_list, obj_csv)

if __name__ == '__main__':
    sys.exit(run())
