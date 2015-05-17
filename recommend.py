import csv
import math
import pprint

class DBError:
    pass

class User():
    def __init__(self, user_id='1', age='24', gender='M', job='technician', zipcode='85711'):
        self.user_id = user_id
        self.age = age
        self.gender = gender
        self.job = job
        self.zipcode = zipcode
        self.ratings = {}
        self.sorted_ratings = []
        self.similar = None
        #self.movies = []

    @classmethod
    def load_users(cls, filename):
        fieldnames = ['user_id','age','gender','job', 'zipcode']
        users = {}
        with open(filename, encoding="windows-1252") as file:
            reader = csv.DictReader(file, delimiter='|', fieldnames=fieldnames)
            for row in reader:
                user_id = row.pop('user_id')
                users[user_id] = User(**row)
        return users

    @classmethod
    def load_ratings(cls, filename, users):
        fieldnames = ['user_id','item_id','rating','timestamp']
        #ratings = {}
        with open(filename, encoding="windows-1252") as file:
            reader = csv.DictReader(file, delimiter='\t', fieldnames=fieldnames)
            for row in reader:
                user_id = row['user_id']
                item_id = row['item_id']
                rating = row['rating']
                try:
                    users[user_id].ratings[item_id] = rating
                except KeyError:
                    assert KeyError("That user_id does not exist")
        return users
    @property
    def movies(self):
        try:
            return [item_id for item_id in self.ratings]
                          #sorted ... key=lambda x: x[1])
        except:
            assert KeyError("No movies found for this user")
    def sort_ratings(self):
        """ """
        sorted_ratings = sorted(self.ratings, key=self.ratings.get, reverse=True)
        self.sorted_ratings = sorted_ratings
        return sorted_ratings

    def my_favorites(self, n=20):
        return [(movie_id, self.ratings[movie_id])
                for movie_id in self.sort_ratings()[:n]]


class Movie():
    item_fieldnames = \
        ['movie_id', 'movie_title', 'release_date', 'video_release_date',
        'IMDb URL', 'unknown', 'Action', 'Adventure', 'Animation',
        "Childrens", 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy',
        'FilmNoir', 'Horror', 'Musical', 'Mystery', 'Romance', 'SciFi',
        'Thriller', 'War', 'Western']

    def __init__(self, **kwargs):
        for prop, val in kwargs.items():
            setattr(self, prop, val)
        self.ratings = {}

    @classmethod
    def load_movies(cls, filename):
        movies = {}
        with open(filename, encoding="windows-1252") as file:
            reader = csv.DictReader(file, delimiter='|', fieldnames=Movie.item_fieldnames)
            for row in reader:
                movie_id = row.pop('movie_id')
                movies[movie_id] = Movie(**row)
        return movies

    @classmethod
    def load_ratings(cls, filename, movies):
        fieldnames = ['user_id','item_id','rating','timestamp']
        #ratings = {}
        with open(filename, encoding="windows-1252") as file:
            reader = csv.DictReader(file, delimiter='\t', fieldnames=fieldnames)
            for row in reader:
                user_id = row['user_id']
                item_id = row['item_id']
                rating = row['rating']
                try:
                    movies[item_id].ratings[user_id] = rating
                except KeyError:
                    movies[item_id] = Movie(ratings={})
                    movies[item_id].ratings[user_id] = rating

                    #raise KeyError("That movie or user id does not exist")
        return movies

    @property
    def users(self):
        try:
            return [user_id for user_id in self.ratings]
        except:
            assert KeyError("No users found for this movie")

    @property
    def num_ratings(self):
        return len(self.ratings)

    @property
    def avg_rating(self):
        return sum([int(val) for val in self.ratings.values()]) / len(self.ratings)


class DataBase():
    def __init__(self, users_file, movies_file, ratings_file):
        my_users = User.load_users(users_file)
        my_users = User.load_ratings(ratings_file, my_users)
        my_movies = Movie.load_movies(movies_file)
        my_movies = Movie.load_ratings(ratings_file, my_movies)

        self.users = my_users
        self.movies = my_movies
        self.similarities = None
        #self.ratings = {}

    def top_n(self, n=20, min_n=2, user=None):
        averages = {movie: self.movies[movie].avg_rating
                    for movie in self.movies
                    if self.movies[movie].num_ratings >= min_n}
        self.averages = []
        for item_id in sorted(averages, key=averages.get, reverse=True):
            self.averages.append((item_id, averages[item_id]))

        if user is None:
            return self.averages[:n]
        else:
            num_ratings = len(self.users[user].ratings)
            averages = self.averages[:n+num_ratings]
            averages = [avg for avg in averages if avg[0] not in self.users[user].movies]
            return averages[:n]
    def intersection(self, me, them):
        v = set(self.users[me].movies)
        w = set(self.users[them].movies)
        return list(v.intersection(w))
        #return [x for x in self.users[me].movies]

    def euclidean_distance(self, me, other):
        """Given two lists, give the Euclidean distance between them on a scale
        of 0 to 1. 1 means the two lists are identical.
        returns dictionary with {distance: and num_shared:}
        """
        s = self.users[me].ratings
        o = self.users[other].ratings
        ixn = self.intersection(me, other)
        num_shared = len(ixn)

        v = []
        w = []

        for movie in ixn:
            #print(repr(movie))
            #print(self.users[me].ratings[movie])
            v.append(int(self.users[me].ratings[movie]))
            w.append(int(self.users[other].ratings[movie]))

        # Guard against empty lists.
        if len(v) is 0:
            return {'dist': 0, 'num_shared': 0}

        # Note that this is the same as vector subtraction.
        differences = [v[idx] - w[idx] for idx in range(len(v))]
        squares = [diff ** 2 for diff in differences]
        sum_of_squares = sum(squares)

        return {'dist': 1 / (1 + math.sqrt(sum_of_squares)), 'num_shared': num_shared}

    def calculate_similarities(self):
        def calculate_pairings():
            users = [user_id for user_id in self.users]

            pairings = set()
            for user1 in users:
                for user2 in users:
                    if user1 != user2:
                        pairings.add(frozenset([user1, user2]))
            return pairings

        # for user in calculate_pairings():
        #     print(user)
        pairings =  calculate_pairings()

        self.similarities = {}

        for pairing in pairings:
            # There must be a better way to do this
            pair = set(pairing)
            user1 = pair.pop()
            user2 = pair.pop()
            self.similarities[(user1, user2)] = self.euclidean_distance(user1, user2)

        return True

    def similar(self, me, n=5, min_matches=3):
        rankings = {}
        if self.similarities is None:
            assert DBError('The similarity scores have not been calculated yet for this database')
        else:
            for similarity in self.similarities:
                if me in similarity:
                    not_me = str(list(filter(me.__ne__, similarity))[0])
                    rankings[not_me] = self.similarities[similarity]
        rankings = {user: rankings[user]['dist'] for user in rankings
                    if rankings[user]['num_shared'] >= n }
        rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:n]
        self.users[me].similar = rankings
        return rankings

    def get_title(self, movie_id):
        try:
            return self.movies[movie_id].movie_title
        except:
            return movie_id
    def translate(self, data, fn):
        """Returns passed list of 2-tuples with item[0] transformed with fn"""
        return [(fn(item[0]), item[1]) for item in data]

    def recommend(self, user_id, n=5, mode='simple', num_users=1):
        if self.users[user_id].similar == None:
            self.similar(user_id, n=5, min_matches=3)
        if mode=='simple': # Return top n rated movies from most similar user
            top_matching_users = self.users[user_id].similar[:num_users]
            top_movies = []
            for user, similarity in top_matching_users:
                for movie, rating in self.users[user].ratings.items():
                    # print('user:{}, similarity:{}, movie:{}, rating:{}'.format(
                    #        user, similarity, movie, rating))
                    top_movies.append((movie, similarity * int(rating)))
            top_movies.sort(key=lambda x: x[1], reverse=True)
            filtered = [(movie,score) for movie,score in top_movies if movie not in self.users[user_id].movies]

            def remove_dupes(a_list):
                existing = []
                output = []
                for movie, score in a_list:
                    if movie not in existing:
                        output.append((movie, score))
                return output

            return filtered[:n] #remove_dupes(filtered)[:n]


            # return [self.get_title(mid)
            #         for mid in self.users[top_matching_user].sort_ratings()
            #         if mid not in self.users[user_id].movies
            #         ][:n]
class Recomendation():
    """
        This class should hold an individual Recommendation object
        A list of them will be stored in each user object
        Implement __le__ for sorting
            Add function to select what the le method is, depending on criteria
        Implement __hash__ to be used for removing duplicates???
        Way to make object remove itself if it's a duplicate and < existing
            or add extra data onto a list?


    """

if __name__ == '__main__':
    db = DataBase(users_file='datasets/ml-100k/uhead.user',
                  movies_file='datasets/ml-100k/uhead.item',
                  ratings_file='datasets/ml-100k/uhead.data')
