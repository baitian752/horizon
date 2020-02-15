import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
# from sklearn.metrics import accuracy_score


datas = np.loadtxt('./data.csv', delimiter=',', skiprows=1)
X = datas[:, 0:-1]
y = datas[:, -1]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=np.random.randint(0, 99))

# X_train, y_train = X, y
rfc = RandomForestClassifier(n_estimators=100, random_state=np.random.randint(0, 99))
rfc.fit(X_train, y_train)
print(rfc.predict(X_test))
print(rfc.predict_proba(X_test))

# y_train_pred = rfc.predict(X_train)
# y_test_pred = rfc.predict(X_test)

# print(accuracy_score(y_train, y_train_pred))
# print(accuracy_score(y_test, y_test_pred))

joblib.dump(rfc, './model.m')