from machine import ADC
numADCreadings = const(1000)
Vmax = const(4240)

def vbatt():
    adc = ADC(0)
    apin = adc.channel(attn=ADC.ATTN_2_5DB, pin='P16')
    samplesADC = [0.0]*numADCreadings
    meanADC = 0.0
    i = 0
    while (i < numADCreadings):
        sample = apin()
        samplesADC[i] = sample
        meanADC += sample
        i += 1
    meanADC /= numADCreadings
    varianceADC = 0.0
    for sample in samplesADC:
        varianceADC += (sample - meanADC)**2
    varianceADC /= (numADCreadings - 1)
    # print("%u ADC readings :\n%s" %(numADCreadings, str(samplesADC)))
    print("Mean of ADC readings (0-4095) = %15.13f" % meanADC)
    print("Mean of ADC voltage readings (0-%dmV) = %15.13f" % (apin.value_to_voltage(4095), apin.value_to_voltage(int(meanADC))))
    print("Variance of ADC readings = %15.13f" % varianceADC)
    print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % ((varianceADC*10**6)//(meanADC**2)))
    return meanADC/4095*Vmax
