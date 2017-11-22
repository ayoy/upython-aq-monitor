import machine
numADCreadings = const(100)
adcVmax = 10**(3/20)

def ADCloopMeanStdDev():
    adc = machine.ADC(0)
    adcread = adc.channel(attn=1, pin='P16')
    samplesADC = [0.0]*numADCreadings
    meanADC = 0.0
    i = 0
    while (i < numADCreadings):
        adcint = adcread()
        samplesADC[i] = adcint
        meanADC += adcint
        i += 1
    meanADC /= numADCreadings
    # varianceADC = 0.0
    # for adcint in samplesADC:
    #     varianceADC += (adcint - meanADC)**2
    # varianceADC /= (numADCreadings - 1)
    # print("%u ADC readings :\n%s" %(numADCreadings, str(samplesADC)))
    # print("Mean of ADC readings (0-4095) = %15.13f" % meanADC)
    # print("Mean of ADC readings (0-1412 mV) = %15.13f" % (meanADC*(adcVmax)/4096))
    # print("Variance of ADC readings = %15.13f" % varianceADC)
    # print("10**6*Variance/(Mean**2) of ADC readings = %15.13f" % ((varianceADC*10**6)//(meanADC**2)))
    return (meanADC*adcVmax/4096)/(56/171)*1000
