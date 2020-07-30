#!/usr/bin/python3
import mysql.connector
import matplotlib.pyplot as plt
import numpy as np

cnx = mysql.connector.connect(user='root', password='admin',
                              host='127.0.0.1',
                              database='promotions')

cursor = cnx.cursor()


def priceByMonth(origin, destination, startingDate, show=False):

    x = []
    priceByMonth = []
    cursor.execute(
        """SELECT STDDEV(adult_price_ttc),AVG(adult_price_ttc) from promoflights WHERE departure_date>="{}" AND origin="{}" AND destination="{}" """.format(startingDate, origin, destination))
    mu, sigma = cursor.fetchone()
    print(mu, sigma)
    cursor.execute(
        """SELECT MONTH(departure_date),AVG(adult_price_ttc) FROM promoflights WHERE departure_date>="{}" AND origin="{}" AND destination="{}" AND adult_price_ttc BETWEEN {} AND {} GROUP BY MONTH(departure_date)""".format(startingDate, origin, destination, mu-2*sigma, mu+2*sigma))
    result = cursor.fetchall()

    for tuple in result:
        x.append(tuple[0])
        priceByMonth.append(tuple[1])
    print("%s -> %s" % (origin, destination))
    print('x =', x)
    print('priceByMonth =', priceByMonth)
    if show:
        plt.title('Price by month {}$\\rightarrow${}'.format(
            origin, destination))
        plt.bar(x, priceByMonth)
        plt.xlabel('Months')
        plt.ylabel('Average price during the month')
        plt.show()


def priceByDay(origin, destination, startingDate, show=False):

    x = []
    priceByDay = []
    cursor.execute(
        """SELECT STDDEV(adult_price_ttc),AVG(adult_price_ttc) from promoflights WHERE departure_date>='{}' AND origin="{}" AND destination="{}" """.format(startingDate, origin, destination))

    mu, sigma = cursor.fetchone()

    cursor.execute(
        """SELECT DAYOFYEAR(departure_date) day_of_year,AVG(adult_price_ttc) FROM promoflights 
            WHERE origin="{}" AND destination="{}" AND adult_price_ttc BETWEEN {} AND {}
            GROUP BY DAYOFYEAR(departure_date) """.format(origin, destination, mu-2*sigma, mu+2*sigma))

    result = cursor.fetchall()
    for tuple in result:
        x.append(tuple[0])
        priceByDay.append(tuple[1])
    print('x =', x)
    print('priceByDay =', priceByDay)
    if show:
        dic = {x[i]: priceByDay[i] for i in range(len(x))}
        xSorted = sorted(dic)
        priceByDaySorted = []
        for xi in xSorted:
            priceByDaySorted.append(dic[xi])

        plt.title('Price by day of travel {}$\\rightarrow${}'.format(
            origin, destination))
        plt.plot(xSorted, priceByDay)
        # plt.plot([1, 365], [mu, mu], color="red")
        # plt.plot([1, 365], [mu-2*sigma, mu-2*sigma], color="green")
        # plt.plot([1, 365], [mu+2*sigma, mu+2*sigma], color="orange")

        plt.xlabel('Days')
        plt.ylabel('Average price during the day')
        plt.show()
    return (x, priceByDay)


def priceByDayRangeDay(origin, destination, dayTrip, startingDate, show=False):
    x = list(range(1, 365-dayTrip))

    cursor.execute(
        """SELECT STDDEV(adult_price_ttc),AVG(adult_price_ttc) from promoflights WHERE departure_date>='{}' -- AND origin="{}" AND destination="{}" """.format(startingDate, origin, destination))
    mu, sigma = cursor.fetchone()

    cursor.execute("""SELECT concat(1+{0}*floor(DAYOFYEAR(departure_date)/{0}), '-', 
        ROUND(0.5*(({0}*FLOOR(DAYOFYEAR(departure_date)/{0}) +{0}+365)-ABS({0}*FLOOR(DAYOFYEAR(departure_date)/{0}) +{0}-365)))) 
        AS `range`,ROUND(AVG(adult_price_ttc),2) AS price from promoflights WHERE adult_price_ttc BETWEEN {4} AND {5} /*AND origin="{1}" AND destination="{2}"*/ AND departure_date>='{3}'  GROUP BY 1 ORDER BY DAYOFYEAR(departure_date)""".format(dayTrip, origin, destination, startingDate, mu-sigma, mu+sigma))
    result = cursor.fetchall()
    x = []
    priceByDayRange = []
    for tuple in result:
        x.append(tuple[0])
        priceByDayRange.append(tuple[1])
    print(x)
    print(priceByDayRange)
    if show:
        plt.title('Price by day range of travel {}$\\rightarrow${} (range={} days)'.format(
            origin, destination, dayTrip))
        plt.bar(x, priceByDayRange)
        plt.xlabel("Days")
        plt.ylabel('Average price between day and day+dayTrip')
        plt.xticks(rotation=45)
        plt.show()


def priceAsDateApproaches(origin, destination, maxDiff, startingDate, maxStops, show=False):
    diffDay = []
    priceByDiff = []
    cursor.execute(
        """SELECT STDDEV(adult_price_ttc),AVG(adult_price_ttc) from promoflights WHERE departure_date>='{}' AND origin="{}" AND destination="{}" """.format(startingDate, origin, destination))
    mu, sigma = cursor.fetchone()
    cursor.execute("""
    SELECT DATEDIFF(departure_date,refresh_date)diff_refresh_departure,AVG(adult_price_ttc) avg_price FROM `promoflights` 
    WHERE adult_price_ttc BETWEEN {} AND {}
    AND origin="{}" AND destination="{}"
    AND DATEDIFF(departure_date,refresh_date)<={} /*AND departure_date>='{}'*/ AND stops<={}
    GROUP BY DATEDIFF(departure_date,refresh_date)
    ORDER BY `diff_refresh_departure` ASC """.format(mu-2*sigma, mu+2*sigma, origin, destination, maxDiff, startingDate, maxStops))
    result = cursor.fetchall()
    for tuple in result:
        diffDay.append(tuple[0])
        priceByDiff.append(tuple[1])
    print(diffDay)
    print(priceByDiff)
    if show:
        plt.title('Price as date approaches of travel {}$\\rightarrow${}'.format(
            origin, destination))
        plt.plot(diffDay, priceByDiff)
        plt.xlabel("Days")
        plt.ylabel('average price')
        # plt.xticks(rotation=45)
        plt.show()


def priceAsDateApproachesMin(origin, destination, maxDiff, startingDate, maxStops, show=False):
    diffDay = []
    priceByDiff = []
    minId = []
    cursor.execute(
        """SELECT STDDEV(adult_price_ttc),AVG(adult_price_ttc) from promoflights WHERE departure_date>='{}' -- AND origin="{}" AND destination="{}" """.format(startingDate, origin, destination))
    mu, sigma = cursor.fetchone()
    cursor.execute("""SELECT t.id id_min,t.datediff datediff,t2.min_price from
        (SELECT DATEDIFF(departure_date,refresh_date) datediff ,adult_price_ttc,id FROM promoflights
        WHERE DATEDIFF(departure_date,refresh_date)<={2} AND departure_date>='{3}' AND stops<={4}
        -- AND origin="{0}" AND destination="{1}"
        ) t
        INNER JOIN
        ( SELECT DATEDIFF(departure_date,refresh_date) datediff, MIN(adult_price_ttc) min_price
          FROM promoflights WHERE DATEDIFF(departure_date,refresh_date)<={2} AND departure_date>='{3}' AND stops<={4}
          -- AND origin="{0}" AND destination="{1}"
          GROUP BY datediff
        ) t2
        ON t.adult_price_ttc = t2.min_price AND t.datediff = t2.datediff
        GROUP by datediff
        ORDER BY `t`.`datediff` ASC""".format(origin, destination, maxDiff, startingDate, maxStops))

    result = cursor.fetchall()
    for tuple in result:
        diffDay.append(tuple[1])
        priceByDiff.append(tuple[2])
        minId.append(tuple[0])

    print(diffDay)
    print(priceByDiff)
    print(minId)

    if show:
        plt.title('Min price as date approaches of travel {}$\\rightarrow${}'.format(
            origin, destination))
        plt.plot(diffDay, priceByDiff)
        plt.xlabel("Days")
        plt.ylabel('average price')
        # plt.xticks(rotation=45)
        plt.show()


priceByMonth("CDG", "LYS", "2019-01-01", show=True)
priceByDay("CDG", "LYS", "2019-01-01", show=True)
priceByDayRangeDay("CDG", "LYS", 80, "2019-01-01", show=True)
priceAsDateApproaches("CDG", "LYS", 10, "2019-01-01", 1, show=True)
priceAsDateApproachesMin("CDG", "LYS", 10, "2019-01-01", 1, show=True)


cnx.close()
