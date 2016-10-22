import zbar
proc = zbar.Processor()
proc.parse_config('enable')
device = '/dev/video0'
proc.init(device)
proc.visible = False
proc.process_one()
for symbol in proc.results:
    # do something useful with results
    print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data