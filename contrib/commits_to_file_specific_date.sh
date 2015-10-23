cd $1
git log --before=$3 --after=$3 --follow $2 | grep -A 2 \^commit
