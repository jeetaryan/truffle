

#migrate isISP and manualISP to companies

SELECT COUNT(*) total, visits.utm_source, CASE WHEN kickfire.isISP OR kickfire.manualISP THEN 1 ELSE 0 END AS ISP FROM visits INNER JOIN kickfire on visits.companyId=kickfire.companyId group by visits.utm_source, ISP order by total DESC;