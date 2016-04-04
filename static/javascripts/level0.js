$(function() {
	var html5 = window.File && window.FileReader && window.FileList && window.Blob;
	if (!html5){
		console.error('Your browser does not support HTML5! Stopped!');
		$('#idContError').css('display','');
		$('#idErrorMessage').text('Your browser does not support HTML5! Stopped!');
		return;
	}

	var $idContainerTop=$('#idContainerTop'),
		$idContFile=$('#idContFile'),
		$idContHash=$('#idContHash'),
		$idContCode=$('#idContCode'),
		MSG1='Opening:',
		MSG2='Calculating:', // Length less than "Last modified:" (14 characters) because of display:table, second column should not move
		gHash='';
	
	var TIMEOUT_MS=25000;
	
	if ($idContainerTop.attr('data-status')=='error'){ 
		return;
	} else {
		$idContFile.css('display','');
	}
	
	
	function updateOnData(data, code){
		if (data){
			if (data['success']==true){
				$('#idInputTextCode').attr('data-code', code);
				
				$idContCode.css('display','none');
				$('#idContError').css('display','none');
				$idContFile.css('display','');	
			} else if (data['success']==false){			 
				$('#idContError').css('display','');
				$('#idErrorMessage').text('Error. '+data['reason']);
			} else {
				$('#idContError').css('display','');
				$('#idErrorMessage').text('Unknown error');
			}
		} else {
			$('#idContError').css('display','');
			$('#idErrorMessage').text('Error. No data received');
		}
	}
	
	function capitalizeFirstLetter(string) {
	    return string.charAt(0).toUpperCase() + string.slice(1);
	}
		
	$('#idCheckCode').on('click', function(){
		var code=$('#idInputTextCode').val();
		$.ajax( '/api/code/check?d='+code,
				{cache:false,
				 timeout: TIMEOUT_MS,
				 success:function(data){
					 	updateOnData(data, code); 	
				 },
				 error:function(xhr, status, err){
					 var statusMod=status?(capitalizeFirstLetter(status)+"."):"",
						 errorThrown=err?(" "+capitalizeFirstLetter(status)):"";
					 
					 $('#idContError').css('display','');
					 $('#idErrorMessage').text(statusMod+errorThrown);
				 }
			  }
		);
	});
	
	function processHash(f){
		$idContFile.css('display', 'none');
		$idContHash.css('display','');
		$('#hValDesc').text(MSG1);

		var nameEscaped=f.name;
		
		nameEscaped = nameEscaped.replace(/\</g,"&lt;");  
		nameEscaped = nameEscaped.replace(/\>/g,"&gt;");
		
		nameEscaped = nameEscaped.replace(/\"/g,"&quot;");
		nameEscaped = nameEscaped.replace(/\'/g,"&apos;");
		
		$('#hName').text(nameEscaped);	
	    $('#hType').text(f.type || 'n/a');
	    $('#hSize').text(f.size + ' bytes');
	    $('#hLM').text(f.lastModifiedDate ? f.lastModifiedDate.toLocaleDateString() : 'n/a');
	    
	    if (f.size>250*1024*1024){
	    	$('#idContError').css('display','');
			$('#idErrorMessage').text('File is bigger than 250 MB. Try a smaller file');
			return;
	    }

	    // FileReader in Chrome: 250 MB max.
	    var reader = new FileReader();
		reader.onload = function(e) {
			var data = e.target.result;
			
			if (data==""){
				console.log('Data is empty!');
				
				$('#idContError').css('display','');
				$('#idErrorMessage').text('File is too big. Try a smaller file');
				
				return;
			} 
			$('#hValDesc').text(MSG2);
			$('#hVal').text('0%');
			
			// We use cryptoProofOfExistence.js
			setTimeout(function() {
				CryptoJS.SHA256(data,crypto_callback,crypto_finish);
			}, 200); 
			// We use cryptoProofOfExistence.js	
		};
		
		reader.onprogress = function(evt) {
		    if (evt.lengthComputable) {
		    	var w = (((evt.loaded / evt.total)*100).toFixed(2));
		    	$('#hValDesc').text(MSG1);
				$('#hVal').text(''+w+'%');
		    }
		}; 
		
		reader.readAsBinaryString(f);
	}
	
	function handleFileSelect(evt) {
	    evt.stopPropagation();
	    evt.preventDefault();

	    var files = evt.dataTransfer.files; // FileList object.
	    processHash(files[0]);
	  }

	  function handleDragOver(evt) {
	    evt.stopPropagation();
	    evt.preventDefault();
	    evt.dataTransfer.dropEffect = 'copy'; // Explicitly show this is a copy.
	  }

	  // Setup the drag and drop listeners.
	  var dropZone = document.getElementById('import-drop-target');
	  dropZone.addEventListener('dragover', handleDragOver, false);
	  dropZone.addEventListener('drop', handleFileSelect, false);
	
	$(function() {
		$("#upContainer").css("visibility","");
	});
	
	$("#import-file-select").on("change", function(e){
		var file=$("#import-file-select")[0]['files'][0];
		processHash(file);
		
		// http://stackoverflow.com/questions/4109276/how-to-detect-input-type-file-change-for-the-same-file 
		// If it doesn't work with attr("value", "") , try with .val("")
		$(this).val(""); 
	});
	

	$('#idCancelPublish').on('click', function(){
		$idContHash.css('display','none');
		$('#idContHashCode').css('display','none');
		$('#hName').text('');
		$('#hType').text('');
		$('#hSize').text('');
		$('#hLM').text('');
		
		$('#idSavePublishContainer').css('display','none');
		$('#idContError').css('display','none');
		$idContFile.css('display','');
	});
	
	$('#showMe').on('click', function(e){		
		$('html, body').animate({
            scrollTop: $(this).offset().top + 'px'
        }, 'fast');
		
		var data=JSON.parse($('#idContHashInfo').attr('data-json')),	
			data2={"txid":data.txid, "merkle":data.merkle};
		$('#merkleChain').text(JSON.stringify(data2, null, 4));
		
		var arrMerkle=data['merkle'],
			txid=data['txid'],
			arrLength=arrMerkle.length,
			self=arrMerkle[0][0],
			rootHash=arrMerkle[arrLength-1][0],
			bashScriptIni='#!/bin/bash\nfunction sha256 {\n\techo -n $1$2 | xxd -r -p | sha256sum | head -c 64\n}\n\n',
			bashScriptMid='self='+self+'\n',
			bashScriptEnd='printf "\\nChain is VALID\\n"\nelse\n\tprintf "\\nError. Chain is INVALID\\n"\nfi\n\n',
			fileName=$('#hName').text();
		
		if (arrLength<2){
			console.error('Fatal error. Impossible situation. Merkle chain length less than 2');
		} else {
			var str1_1='self='+self+'\nif [ $(sha256sum "'+fileName+'" | head -c 64) == $self ]; then printf "\nOK. Hash MATCHES document\n"; else printf "\nERROR. Hash DOES NOT MATCH document\n"; fi';
			$('#bashScript1').text(str1_1);
			$('#self').text(self);
			
			var prev='$self';
			for (var i=1;i<arrLength-1;i++){
				var args=['',''];
				if (arrMerkle[i][1]=='L'){
					bashScriptMid+='hashL'+i+'='+arrMerkle[i][0]+'\n';
					args[0]='$hashL'+i;
					args[1]=prev;
				} else { // 'R'
					bashScriptMid+='hashR'+i+'='+arrMerkle[i][0]+'\n';
					args[0]=prev;
					args[1]='$hashR'+i;
				}
				prev='$(sha256 '+args[0]+' '+args[1]+')';
			}
			bashScriptMid+='root='+rootHash+'\n\n';
			$('#bashScript2').text(bashScriptIni+bashScriptMid+'if [ '+prev+' == $root ]; then\n\t'+bashScriptEnd);			
			
			var url='https://www.blocktrail.com/BTC/tx/'+txid;
			$('#webTxid').attr('href', url).text(url);
			
			var str1='root='+rootHash,
				str2='rootBitcoin=$(curl "https://api.blocktrail.com/v1/btc/transaction/'+txid+'?api_key=MY_APIKEY" | grep -Po \'"script":.*?[^\\\\]",\' | grep -Po \'".*?"\' | tail -1 | sed \'s/"//g\' | tr -d [:space:] | tail -c 64)',
				str3='if [ $rootBitcoin == $root ]; then printf "\\nOK\\n"; else printf "\\nERROR\\n"; fi ',
				strFinal=str1+'\n'+str2+'\n\n'+str3+'\n';
			$('#bashScript3').text(strFinal);
		}
		
		$('#explainShowMe').css('display','');
        return this;
		
	});
	
	
	$('#merkleJson').on('click', function(){
		var data=JSON.parse($('#idContHashInfo').attr('data-json')),	
			data2={"txid":data.txid, "merkle":data.merkle};	
		saveAs(new Blob([JSON.stringify(data2, null, 4)], {type: "application/json;charset=utf-8"}), "BitcoinMerkle_"+data.merkle[0][0]+".txt");
		
	});
	
	function crypto_callback(p) {
		// ProofOfExistence
		var w = ((p*100).toFixed(0));
		$('#hValDesc').text(MSG2);
		$('#hVal').text(''+w+'%');
	}

	function crypto_finish(hash) {
		gHash=hash;
		$('#hValDesc').text('ID SHA256:');
		$('#hVal').text(hash);
		
		// https://github.com/maraoz/proofofexistence/issues/12
		if (hash=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'){ // Hash of empty string. Most likely file too big 
			$('#idContError').css('display','');
			$('#idErrorMessage').text('File is bigger than 250 MB. Try a smaller file');
			return;
		}
		
		$('#idSavePublishContainer').css('display','');
		$('#idContHashCheckExistence').css('display','');
		
		$.ajax( '/api/content/check?hash='+gHash, {	cache:false,
			 												timeout: TIMEOUT_MS,
			 												success: function (data){
			 													$('#idContHashCheckExistence').css('display','none');
			 													
			 													var $idContHashNew=$('#idContHashNew'),
			 														$idContHashWaitingForBroadcast=$('#idContHashWaitingForBroadcast'),
			 														$idContHashAlreadyBroadcast=$('#idContHashAlreadyBroadcast'),
			 														$idContError=$('#idContError');
			 													
			 													if (data){
			 														if (data['success']==true){
			 															$idContError.css('display', 'none');
			 															$('#idContHashInfo').attr('data-json',JSON.stringify(data));
			 															if (data['stat']==0){
			 																var dateStr=data['date'];
			 																$idContHashNew.css('display','');
			 																$idContHashWaitingForBroadcast.css('display', 'none');
			 																$idContHashAlreadyBroadcast.css('display', 'none');
			 																$('#timeReceived').text(dateStr.substring(11,19));
			 																$('#today1').text(dateStr.substring(0,10));
			 																
			 																$('#docHash').text(gHash);
			 																
			 															} else if (data['stat']==1){
			 																var dateStr=data['date'];
			 																$idContHashNew.css('display','none');
			 																$idContHashWaitingForBroadcast.css('display', '');
			 																$idContHashAlreadyBroadcast.css('display', 'none');
			 																
			 																$('#docHash').text(gHash);
			 																$('#dateReceived1').text(dateStr);
			 																$('#today2').text(dateStr.substring(0,10));
			 																
			 															} else if (data['stat']==2){
			 																$idContHashNew.css('display','none');
			 																$idContHashWaitingForBroadcast.css('display', 'none');
			 																$idContHashAlreadyBroadcast.css('display', '');
			 																
			 																var txid=data['txid'];
			 																var url='https://www.blocktrail.com/BTC/tx/'+txid;
			 																$('#webTxid2').attr('href', url).text(url);
			 															} else {
			 																console.error('Impossible! stat must be 0, 1 or 2.');
			 															}
			 														} else if (data['success']==false) {
			 															$idContError.css('display', '');
			 															$idContHashNew.css('display','none');
		 																$idContHashWaitingForBroadcast.css('display', 'none');
		 																$idContHashAlreadyBroadcast.css('display', 'none');
		 																
		 																$('#idErrorMessage').text(data['reason']);
			 														} else {
			 															console.error('Impossible! checkContentHash, Unknown error.');
			 														}
			 													} else {
			 														console.error('checkContentHash. Error. No data received.');
			 													}
			 												},
			 												error: function (xhr, status, err){
			 													console.error("Inside ajax error, checkContentHash");
			 													console.error('xhr: '+xhr);
			 													console.error('status: '+status);
			 													console.error('err: '+err);
			 												}
			 											  });
	}
	
	function updatePublishedStatus(data){
		if (data){
			if (data['success']==true){
				var txid=data['txid'];
				
				$('#idContHash').css('display','none');
				$('#idContTxid').css('display','');
				
				$('#idUniqueId').text(gHash);
				$('#idTxid').text(txid);
				
				$('#idBcastDateRow').css('display','none');
				var url='https://www.blocktrail.com/BTC/tx/'+txid;
				$('#idLink').html('<a target="_blank" href="'+url+'">'+url+'</a>');
				
				$('#idContTxidWarn').css('display','');
			} else if (data['success']==false) {
				$('#idContError').css('display','');
				$('#idErrorMessage').text('Error. '+data['reason']);
			} else {
				$('#idContError').css('display','');
				$('#idErrorMessage').text('Unknown error');
			}
		} else {
			$('#idContError').css('display','');
			$('#idErrorMessage').text('Error. No data received');
		}
	}
});




