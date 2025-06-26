for dbtype in {"postgres","aurora-postgres"}; do
IFS=$'\n'
    for sdmdb in $(sdm status --filter "tags:dbe=true type:${dbtype}" | grep dbeadmin | grep -v DATASOURCE | \
      grep -v saturn | grep -v datawarehouse | sort); do

        sdmname=$(echo ${sdmdb} | awk '{split($0, array, "  *"); print array[2]}')

            if [[ ${sdmdb} =~ ^(.*not connected.*)$ ]]; then
                export sdmport=$( echo ${sdmdb} | awk '{split($0, array, "  *"); print array[5]}' )
                echo ${sdmport}
            else
                export sdmport=$( echo ${sdmdb} | awk '{split($0, array, "  *"); print array[4]}' )
                echo ${sdmport}
            fi
done
done 