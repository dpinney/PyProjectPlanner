'''
Chart a program budget.
Key questions this answers: how much work do we have, are we doing it, who is doing it, how much more work do we need?
'''

import matplotlib.pyplot as plt
from datetime import datetime as dt, timedelta as td
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib
import csv
import sys

def csvTaskImport(filePath):
	# Pull in a CSV with a list of tasks.
	def tryCon(field):
		# Convert to Python types.
		if field.isdigit():
			return int(field)
		else:
			try:
				return dt.strptime(field,'%Y-%m-%d')
			except:
				return field
	projects = []
	with open(filePath,'r') as inFile:
		reader = csv.reader(inFile, delimiter=',')
		headers = reader.next()
		for row in reader:
			projects.append({headers[i]:tryCon(field) for (i,field) in enumerate(row)})
	# TODO: do better validation.
	validProjects = [x for x in projects if x.get('status','')!='']
	return sorted(validProjects, key=lambda p:p['start'])

def drawBudgetChart(tasks, updateDt):
	projects = list()
	projNames = set([x['project'] for x in tasks])
	for pName in projNames:
		allProjTasks = [x for x in tasks if x['project'] == pName]
		newProj = {
			'name':pName,
			'start':min([x['start'] for x in allProjTasks]),
			'end':max([x['end'] for x in allProjTasks]),
			'budget':sum([x['budget'] for x in allProjTasks]),
			'status':allProjTasks[0]['status'],
			'spend':sum([x['spend'] for x in allProjTasks]) }
		projects.append(newProj)
	projects = sorted(projects, key=lambda x:x['start'])
	# Helper functions for date arithmetic.
	def monthsBetween(start, end):
		return (end.year - start.year)*12 + end.month - start.month
	def monthlyBudget(p):
		return 1.0 * p['budget'] / monthsBetween(p['start'], p['end'])
	# General bounds for things.
	totalBudget = sum([monthlyBudget(p) for p in projects])
	earliestStart = min([p['start'] for p in projects])
	latestEnd = max([p['end'] for p in projects])
	totalTime = latestEnd - earliestStart
	# Dicts for mapping project status to color.
	statusMap = {'complete':'dodgerblue','working':'green','proposed':'orange'}
	spendMap = {'complete':'blue', 'working':'darkgreen', 'proposed':'darkorange'}
	# Set up the timeline chart.
	fig = plt.figure(figsize=(10,7.5), dpi=80)
	ax1 = plt.axes([0.05,0.3,0.94,0.65])
	plt.title('Plot created on ' + dt.now().date().isoformat() + ' with spend data from ' + updateDt.date().isoformat(), fontsize=10)
	# Draw each project:
	for (i,p) in enumerate(projects):
		currBottom = sum([monthlyBudget(p2) for p2 in projects[0:i]])
		# Full budget:
		ax1.bar(
			left=p['start'],
			bottom=currBottom,
			height=monthlyBudget(p),
			width=(p['end']-p['start']).days,
			orientation='horizontal',
			color=statusMap.get(p['status'],'gray'),
			edgecolor='white')
		# Current spend:
		ax1.bar(
			left=p['start'],
			bottom=currBottom,
			height=monthlyBudget(p),
			width=(p['end']-p['start']).days*(1.0*p['spend']/p['budget']),
			orientation='horizontal',
			color=spendMap.get(p['status'],'gray'),
			edgecolor='white')
		# Spend title:
		if monthlyBudget(p) > 0.015 * totalBudget:
			ax1.text(x=p['start'], y=currBottom+0.005*totalBudget, s=' ' + p['name'], color='white', size=3)
	# Set up the axis labels.
	ax1.yaxis.set_visible(False)
	ax1.xaxis.set_visible(False)
	plt.ylim(0,totalBudget)
	vertLine = ax1.axvline(x=dt.now(), color='red', linestyle='--')
	ax1.legend( # Hack: we make zero size bars to get the colors right...
		(ax1.bar(0,0,color=statusMap['complete'],edgecolor='white'),
			ax1.bar(0,0,color=statusMap['working'],edgecolor='white'),
			ax1.bar(0,0,color=statusMap['proposed'],edgecolor='white')),
		('Complete','Working','Proposed'),
		loc='upper left',
		fontsize=8,
		frameon=False)
	# Draw the total approved versus proposed budget chart.
	ax2 = plt.axes([0.05,0.05,0.94,0.22], sharex=ax1)
	totalMonths = monthsBetween(earliestStart, latestEnd)
	(iMonth, iYear) = (earliestStart.month, earliestStart.year)
	for month in xrange(totalMonths+1):
		(currMonth, currYear) = (iMonth, iYear)
		currDate = dt(currYear,currMonth,1)
		# Iterate next month/year:
		if iMonth == 12:
			iYear += 1
			iMonth = 1
		else:
			iMonth += 1
		# Draw amounts.
		budgeted = 0
		proposed = 0
		for p in projects:
			if p['start'] <= currDate and p['end'] > currDate:
				if p['status'] == 'proposed': proposed += monthlyBudget(p)
				else: budgeted += monthlyBudget(p)
		# Budgeted.
		ax2.bar(left=currDate, bottom=0, height=budgeted, width=(dt(iYear,iMonth,1)-currDate).days, edgecolor='white', color='gray')
		# Proposed.
		ax2.bar(left=currDate, bottom=budgeted, height=proposed, width=(dt(iYear,iMonth,1)-currDate).days, edgecolor='white', color='darkgray')
	# X axis settings.
	ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
	ax2.xaxis.set_major_locator(mdates.YearLocator())
	plt.xlim(min([p['start'] for p in projects]).toordinal(),max([p['end'] for p in projects]).toordinal())
	# Y axis settings.
	def thousands(x, pos):
		return '%1.0f' % (x*1e-3)
	formatter = matplotlib.ticker.FuncFormatter(thousands)
	ax2.yaxis.set_major_formatter(formatter)
	ax2.legend(('Funded','Bid'),loc='upper left', fontsize=8, frameon=False)
	plt.setp(plt.yticks()[1], fontsize=8)
	plt.ylabel('Monthly Spend (k$)', fontsize=8)
	return fig

def drawUtilizationChart(tasks):
	# All people mentioned in the tasks.
	people = list(set([p['owner'] for p in tasks]))
	# Years between earliest start and latest end inclusive.
	years = range(min([p['start'] for p in tasks]).year, max([p['end'] for p in tasks]).year+1)
	# Map project name and person name to share.
	def percInYear(pObj, year):
		# For a given project (pObj) and year, return the percentage of performance in that year.
		yearJan = dt(year,1,1)
		yearDec = dt(year,12,31)
		pLen = float((pObj['end'] - pObj['start']).days)
		if pObj['start'] >= yearDec or pObj['end'] <= yearJan:
			# Project outside the year.
			return 0.0
		elif pObj['start'] >= yearJan and pObj['end'] <= yearDec:
			# Project inside the year.
			return 1.0
		elif pObj['start'] <= yearJan and pObj['end'] <= yearDec:
			# Project starts earlier, ends in year.
			return (pObj['end'] - yearJan).days / pLen
		elif pObj['start'] >= yearJan and pObj['end'] >= yearDec:
			# Project starts in year, ends in a following year.
			return (yearDec - pObj['start']).days / pLen
		elif pObj['start'] <= yearJan and pObj['end'] >= yearDec:
			# Starts and ends beyond the bounds of the year:
			return 365.0 / pLen
	plt.figure(figsize=(10,7.5), dpi=80)
	for y in years:
		for p in people:
			plt.subplot2grid([len(people),len(years)], [people.index(p),years.index(y)])
			plt.ylim([0, 2500])
			plt.xticks([])
			plt.yticks([])
			if people.index(p) == 0:
				plt.title(str(y))
			if years.index(y) == 0:
				plt.ylabel(p, fontsize=6)
			plt.axhline(y=2000, xmin=0, xmax=1, linewidth=0.5, color = 'gray', ls='dashed')
			pastHeights = 0
			for t in tasks:
				if t['owner'] == p:
					projHours = (t['budget'] * percInYear(t,y)) / t['rate']
					myColor = 'gray'
					if pastHeights + projHours > 2000:
						myColor = 'red'
					plt.bar(1, projHours, bottom=pastHeights, color=myColor, linewidth=0.5)
					if projHours > 200:
						plt.text(x=1.03, y=pastHeights + 50, s=t['project'] + ' - ' + str(int(projHours)), color='white', size=4)
					pastHeights += projHours

def saveCombinedCharts(csvName, outName):
	with PdfPages(outName) as pdf:
		allTasks = csvTaskImport(csvName)
		drawBudgetChart(allTasks, dt(2015,5,1))
		pdf.savefig(bbox_inches='tight')
		plt.close()
		drawUtilizationChart(allTasks)
		pdf.savefig(bbox_inches='tight')
		plt.close()
		d = pdf.infodict()
		d['Title'] = 'Multipage PDF Example'
		d['CreationDate'] = dt.today()

def main():
	if len(sys.argv) < 3:
		print 'Usage: PyProjectPlanner inputFile.csv outputName.pdf.\n' +\
			'No input and output files specified. Attempting to run tests.'
		inName = './testTasksArtisinalSandwich.csv'
		outName = './testOutputSandwichProject.pdf'
	else:
		inName = sys.argv[1]
		outName = sys.argv[2]
	saveCombinedCharts(inName, outName)

if __name__ == '__main__':
	main()
