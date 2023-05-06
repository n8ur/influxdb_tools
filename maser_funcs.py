
# Note: these functions do not return the measure_name or
# location.  These are prepended in the calling function
#
# update 06May2023: Ole Peter Ronningen found two undocumented
# fields in the kvd return (h_press and dis_volts) so those have
# been added here
#
# also correct typo from "cav_base_mistmatch" to
# "cav_base_mismatch"

def rss_func(t, fields):
    msg = \
            " 5MHz_#1_level=" + str(fields[0]) + \
            ",5MHz_#2_level=" + str(fields[1]) + \
            ",10MHz_#1_level=" + str(fields[2]) + \
            ",10MHz_#2_level=" + str(fields[3]) + \
            ",100MHz_level=" + str(fields[4]) + \
            ",2048kHz_level=" + str(fields[5]) + \
            " " + t + \
            "\n"
    return msg

def pwr_func(t, fields):
    msg = \
            " bat_vdc=" + str(fields[0]) + \
            ",ext_27_vdc=" + str(fields[1]) + \
            ",int_27vdc=" + str(fields[2]) + \
            ",int+15vdc=" + str(fields[3]) + \
            ",int-15vdc=" + str(fields[4]) + \
            ",int+5vdc=" + str(fields[5]) + \
            " " + t + \
            "\n"
    return msg

def kvd_func(t, fields):
    msg = \
            " ion_volts=" + str(fields[0]) + \
            ",ion_current=" + str(fields[1]) + \
            ",pur_volts=" + str(fields[2]) + \
            ",pur_current=" + str(fields[3]) + \
            ",h_press=" + str(fields[4]) + \
            ",hfo_current=" + str(fields[5]) + \
            ",hfo_volts=" + str(fields[6]) + \
            ",dis_volts=" + str(fields[7]) + \
            " " + t + \
            "\n"
    return msg

def fll_func(t, fields):
    msg = \
            " 2nd_harm=" + str(fields[0]) + \
            ",xtal_dac=" + str(fields[1]) + \
            ",resonator_dac=" + str(fields[2]) + \
            ",afc_tmp=" + str(fields[3]) + \
            ",if_level=" + str(fields[4]) + \
            ",synth_output=" + str(fields[5]) + \
            ",synth_dac=" + str(fields[6]) + \
            " " + t + \
            "\n"
    return msg

def thr_func(t, fields):
    msg = \
            " cav_side_mismatch=" + str(fields[0]) + \
            ",cav_side_pwr=" + str(fields[1]) + \
            ",cav_base_mismatch=" + str(fields[2]) + \
            ",cav_base_pwr=" + str(fields[3]) + \
            ",h_src_mismatch=" + str(fields[4]) + \
            ",h_src_pwr=" + str(fields[5]) + \
            " " + t + \
            "\n"
    return msg

def navstat_func(t, fields):
    msg = \
            " status=" + str(fields[0]) + \
            " " + t + \
            "\n"
    return msg

def ppsmea_func(t, fields):
    # fields: N0, C0, Nc, C, Nf, dF, STOP/MEASURE, R,
    # n, s, phi, NSN
    # Guess what?  the "STOP/MEASURE" field
    # goes away when we're measuring.
    # we're going to strip their tag and supply
    # our own, just to help document the code
    count = 0
    #print("fields going in to ppsmea_func:")
    #print(fields)
    if fields[6][:2] == "R=":
        fields.insert(6,"MEASURING")

    for x in fields:
        if '=' in x:
            fields[count] = x.split('=')[-1]
        count  = count + 1

    msg = \
            " N0=" + str(fields[0]) + \
            ",C0=" + str(fields[1]) + \
            ",Nc=" + str(fields[2]) + \
            ",C=" + str(fields[3]) + \
            ",Nf=" + str(fields[4]) + \
            ",dF=" + str(fields[5]) + \
            ",measure_state=\"" + str(fields[6]) + "\"" \
            ",R=" + str(fields[7]) + \
            ",n=" + str(fields[8]) + \
            ",s=" + str(fields[9]) + \
            ",phi=" + str(fields[10]) + \
            ",NSN=" + str(fields[11]) + \
            " " + t + \
            "\n"
    return msg

def esynsig_func(t, fields):
    msg = \
            " synsig=" + fields[0] + \
            " " + t + "\n"
    return msg

def synth_func(t, fields):
    msg = \
            " freq=" + str(fields[0]) + \
            " " + t + \
            "\n"
    return msg

def stat_func(t, fields):
    stat_int = int(fields[0])
    # in below, slice reverses to put LSB first
    stat_bin = format(stat_int,'032b')[::-1]
    msg = \
            " stat_word_dec=\"" + str(stat_int) + "\""

    if len(fields) > 1:
        stat_msg = stat_msg_bits + ",diag=\"" + str(fields[1]) + "\"" \
        " " + t + "\n"
    else:
        stat_msg = stat_msg_bits + " " + t + "\n"
    return msg
