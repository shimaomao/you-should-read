#!/usr/bin/env python
import asyncio

import asyncpg


class Item:
    def __init__(self, name, rating_count, rating_total):
        self.name = name
        self.rating_count = float(rating_count or 0)
        self.rating_total = float(rating_total or 0)
        self.bayes = 0

    def rating_average(self):
        try:
            return self.rating_total / self.rating_count
        except ZeroDivisionError:
            return 0

    def rating_bayesian(self, prior_count, prior_average):
        numerator = prior_average + self.rating_total
        denominator = prior_count + self.rating_count
        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0


class Set():
    def __init__(self, items):
        self.items = items
        assert self.items

    def average_rating(self):
        total = sum(i.rating_total for i in self.items)
        count = sum(i.rating_count for i in self.items)
        return total / count

    def average_rating_average(self):
        total = sum(i.rating_average() for i in self.items)
        return total / len(self.items)

    def average_rating_count(self):
        total = sum(i.rating_count for i in self.items)
        return total / len(self.items)

    def average_rating_total(self):
        total = sum(i.rating_total for i in self.items)
        return total / len(self.items)

    def average_rating_total_average(self):
        return self.average_rating_average() * self.average_rating_count()

    def apply(self):
        # ar = self.average_rating()
        ara = self.average_rating_average()
        arc = self.average_rating_count()
        # art = self.average_rating_total()
        # arta = self.average_rating_total_average()

        # print('{:<6}, {:<6}, {:<6}, {:<6}, {:<6}'.format(
        #     round(ar, 4), round(ara, 4), round(arc, 4), round(art, 4),
        #     round(arta, 4)))

        for item in self.items:
            # # (C, A): expect items to have average rating A with confidence C
            # # eg. after C ratings expect average value A
            # item.bayes = round(item.rating_bayesian(3, 5), 3)

            # # smooth from expected values and emphasize dupes
            # item.bayes = round(item.rating_bayesian(arc, art), 3)

            # stronger smoothing and dupes (ara is more centroid)
            item.bayes = round(item.rating_bayesian(arc, ara), 3)

    def score(self):
        print('{:37} | Count | Average | Bayesian'.format('Item'))
        print('{:37} | ----- | ------- | --------'.format('-' * 37))
        for item in sorted(self.items, key=lambda x: -x.rating_average()):
            avg = round(item.rating_average(), 3)
            print('{:37} | {:5} | {:<7} | {:<8}'.format(
                item.name, item.rating_count, avg, item.bayes))


async def main():
    conn = await asyncpg.connect(host='localhost', user='postgres',
                                 database='postgres')
    # TODO: normalize by user?
    items = await conn.fetch(
        """ SELECT m.id, m.name, COUNT(r.value), SUM(r.value)
            FROM ysr.media m
            LEFT JOIN ysr.rating r ON r.mid = m.id
            GROUP BY m.id, m.name
        """)

    s = Set([Item(r[1], r[2], r[3]) for r in items])
    s.apply()
    s.score()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
