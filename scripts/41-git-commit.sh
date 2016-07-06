#!/bin/sh

# commit all changes to gxd

set -e

BRANCH=$1

cd $GXD

if [ -n "$BRANCH" ] ; then
    git checkout master
    git checkout -b $BRANCH || git checkout $BRANCH
    git add .
    git commit -m "incoming for $TODAY"
    git push --set-upstream origin $BRANCH

    # submit pull request
    git request-pull master ${GITURL} $BRANCH
    git checkout master

#    git merge $BRANCH
#    git branch -d $BRANCH
else 
    git add .
    git commit -m "incoming for $TODAY"
fi

